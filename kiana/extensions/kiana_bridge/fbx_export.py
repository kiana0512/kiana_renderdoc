"""ASCII FBX 7.4 export of a captured input-assembly draw (Python 3.6+).

Coordinates and UVs are preserved. Shader deformation, rigs and material intent
cannot be recovered from vertex inputs. A manifest records these limitations,
attribute choices and every texture binding, including export errors.
"""
import json
import math
import os
import re
import struct
import tempfile

import renderdoc as rd


def action_at(actions, event):
    for action in actions:
        if action.eventId == event:
            return action
        found = action_at(action.children, event)
        if found:
            return found
    return None


def triangles(indices, topology, restart=None):
    result, run = [], []
    def flush():
        if topology == "TriangleList":
            if len(run) % 3:
                raise ValueError("Incomplete triangle list")
            result.extend(tuple(run[i:i+3]) for i in range(0, len(run), 3))
        elif topology == "TriangleStrip":
            for i in range(2, len(run)):
                tri = (run[i-2], run[i-1], run[i]) if i % 2 == 0 else (run[i-1], run[i-2], run[i])
                if len(set(tri)) == 3:
                    result.append(tri)
        else:
            raise ValueError("Unsupported topology: " + topology)
    for index in indices:
        if restart is not None and index == restart:
            flush()
            run = []
        else:
            run.append(index)
    flush()
    return result


def decode(data, offset, fmt):
    kind, width, count = str(fmt.compType), int(fmt.compByteWidth), int(fmt.compCount)
    kind = kind.rsplit(".", 1)[-1]
    typ = str(fmt.type).rsplit(".", 1)[-1]
    if typ == "R10G10B10A2":
        word = struct.unpack_from("<I", data, offset)[0]
        values = [(word >> shift) & ((1 << bits)-1) for shift, bits in ((0,10),(10,10),(20,10),(30,2))]
        if kind in ("SInt", "SNorm"):
            values = [v - (1 << b) if v & (1 << (b-1)) else v for v,b in zip(values, (10,10,10,2))]
        if kind == "UNorm":
            values = [v / float((1 << b)-1) for v,b in zip(values, (10,10,10,2))]
        elif kind == "SNorm":
            values = [max(-1.0, v / float((1 << (b-1))-1)) for v,b in zip(values, (10,10,10,2))]
    elif typ == "Regular":
        formats = {("Float",2):"e", ("Float",4):"f", ("Float",8):"d"}
        for b,c in ((1,"B"),(2,"H"),(4,"I")):
            for k in ("UInt", "UNorm", "UScaled"):
                formats[k,b] = c
            for k in ("SInt", "SNorm", "SScaled"):
                formats[k,b] = c.lower()
        char = formats.get((kind,width))
        if not char:
            raise ValueError("Unsupported component format: %s/%s" % (kind,width))
        values = list(struct.unpack_from("<" + str(count) + char, data, offset))
        if kind == "UNorm":
            values = [v / float((1 << (width*8))-1) for v in values]
        elif kind == "SNorm":
            values = [max(-1.0, v / float((1 << (width*8-1))-1)) for v in values]
    else:
        raise ValueError("Unsupported vertex format: " + typ)
    if getattr(fmt, "BGRAOrder", lambda: False)():
        values[0], values[2] = values[2], values[0]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite vertex attribute")
    return values


def extract_mesh(ctrl, action, position_name="", attribute_map=None):
    ps = ctrl.GetPipelineState()
    vbs = ps.GetVBuffers()
    topology = str(ps.GetPrimitiveTopology()).rsplit(".",1)[-1]
    count = int(action.numIndices)
    if count <= 0 or count > 12000000:
        raise ValueError("Empty draw or export index limit exceeded (12 million)")
    indexed = bool(action.flags & rd.ActionFlags.Indexed)
    restart = None
    if indexed:
        ib = ps.GetIBuffer()
        width = int(ib.byteStride)
        if width not in (1,2,4):
            raise ValueError("Invalid index width")
        data = ctrl.GetBufferData(ib.resourceId, ib.byteOffset + int(action.indexOffset)*width, count*width)
        if len(data) != count*width:
            raise ValueError("Truncated index buffer")
        indices = list(struct.unpack("<%d%s" % (count, {1:"B",2:"H",4:"I"}[width]), data))
        if ps.IsRestartEnabled():
            restart = int(ps.GetRestartIndex()) & ((1 << (width*8))-1)
        tris = triangles(indices, topology, restart)
        tris = [tuple(v + int(action.baseVertex) for v in t) for t in tris]
    else:
        tris = triangles(range(int(action.vertexOffset), int(action.vertexOffset)+count), topology)
    if not tris:
        raise ValueError("No non-degenerate triangles")
    original = sorted(set(v for t in tris for v in t))
    if original[0] < 0:
        raise ValueError("Negative vertex index after baseVertex")
    remap = dict((v,i) for i,v in enumerate(original))
    # SWIG array iteration returns borrowed elements. Keep their owning array
    # alive for the entire extraction, including the format child objects.
    inputs = ps.GetVertexInputs()
    attrs = [a for a in inputs if not a.perInstance]
    attribute_map = attribute_map or {}
    position_name = position_name or attribute_map.get("position", "")
    inferred = False
    positions = [a for a in attrs if (a.name == position_name if position_name else
                 re.search(r"(^|_)(position|pos)(\d|$)", a.name, re.I) and "sv_" not in a.name.lower())]
    if not positions and not position_name:
        positions = [a for a in attrs if a.format.compType == rd.CompType.Float and a.format.compCount == 3]
        inferred = len(positions) == 1
    if len(positions) != 1:
        raise ValueError("Position attribute ambiguous. Set position_attribute. Available: " + ", ".join(a.name for a in attrs))
    chosen = [("position", positions[0], 3)]
    for key, pattern, components, limit in (("normal",r"normal|norm",3,1),
                                           ("tangent",r"tangent",3,1),
                                           ("uv",r"texcoord|uv",2,3),
                                           ("color",r"colou?r",4,1)):
        candidates = [a for a in attrs if re.search(pattern, a.name, re.I)]
        chosen.extend((key + str(i) if key == "uv" else key,a,components) for i,a in enumerate(candidates[:limit]))
    swizzles = {}
    for key, name in attribute_map.items():
        if key == "position":
            continue
        if key not in ("normal","tangent","color","uv0","uv1","uv2"):
            raise ValueError("Unknown attribute map key: " + key)
        if ":" in name:
            name, swizzle = name.rsplit(":",1)
            if not swizzle or any(c not in "xyzw" for c in swizzle):
                raise ValueError("Invalid attribute swizzle")
            swizzles[key] = ["xyzw".index(c) for c in swizzle]
        matching = [a for a in attrs if a.name == name]
        if len(matching) != 1:
            raise ValueError("Attribute not available: " + name)
        chosen = [c for c in chosen if c[0] != key]
        chosen.append((key,matching[0],2 if key.startswith("uv") else 4 if key == "color" else 3))
    mesh = {"triangles": [tuple(remap[v] for v in t) for t in tris], "attributes": {}, "warnings": []}
    if inferred:
        mesh["warnings"].append("Inferred position from the unique float3 attribute: " + positions[0].name)
    mesh["available_attributes"] = [{"name":a.name,"format":a.format.Name()} for a in attrs]
    cache = {}
    for key, attr, components in chosen:
        try:
            if attr.vertexBuffer < 0 or attr.vertexBuffer >= len(vbs):
                raise ValueError("vertex buffer %d is not bound (%d available)" % (attr.vertexBuffer,len(vbs)))
            vb = vbs[attr.vertexBuffer]
            stride = int(vb.byteStride)
            start = int(vb.byteOffset) + original[0]*stride
            size = (original[-1]-original[0])*stride + int(attr.byteOffset) + 32
            if size > 512*1024*1024:
                raise ValueError("Vertex buffer range exceeds 512 MiB")
            cache_key = (str(vb.resourceId), start, size)
            if cache_key not in cache:
                cache[cache_key] = ctrl.GetBufferData(vb.resourceId, start, size)
            rows = []
            for v in original:
                values = decode(cache[cache_key], (v-original[0])*stride + int(attr.byteOffset), attr.format)
                if key in swizzles:
                    values = [values[i] for i in swizzles[key]]
                if len(values) < min(components,3):
                    raise ValueError("Not enough attribute components")
                values += [1.0] * (components-len(values))
                rows.append(values[:components])
            mesh[key] = rows
            mesh["attributes"][key] = attribute_map.get(key,attr.name)
        except (ValueError, IndexError, struct.error) as e:
            if key == "position":
                raise
            mesh["warnings"].append("Skipped %s: %s" % (attr.name,e))
    return mesh


def write_fbx(path, mesh):
    def array(name, values):
        vals = list(values)
        return '%s: *%d {\n a: %s\n}\n' % (name,len(vals),','.join(format(v,'.9g') if isinstance(v,float) else str(v) for v in vals))
    text = '; FBX 7.4.0 project file\nFBXHeaderExtension: {\n FBXHeaderVersion: 1003\n FBXVersion: 7400\n Creator: "Kiana RenderDoc"\n}\n'
    text += 'GlobalSettings: {\n Version: 1000\n Properties70: {\n P: "UpAxis", "int", "Integer", "",1\n P: "UpAxisSign", "int", "Integer", "",1\n P: "FrontAxis", "int", "Integer", "",2\n P: "FrontAxisSign", "int", "Integer", "",-1\n P: "CoordAxis", "int", "Integer", "",0\n P: "CoordAxisSign", "int", "Integer", "",1\n P: "UnitScaleFactor", "double", "Number", "",1\n }\n}\n'
    text += 'Objects: {\n Geometry: 1001, "Geometry::CapturedMesh", "Mesh" {\n GeometryVersion: 124\n'
    text += array('Vertices',(v for row in mesh['position'] for v in row))
    text += array('PolygonVertexIndex',(v for a,b,c in mesh['triangles'] for v in (a,b,-c-1)))
    layers = {}
    for key, typ, field in (("normal","Normal","Normals"),("tangent","Tangent","Tangents"),
                            ("color","Color","Colors"),("uv0","UV","UV"),("uv1","UV","UV"),("uv2","UV","UV")):
        if key not in mesh:
            continue
        idx = int(key[-1]) if key.startswith('uv') else 0
        text += 'LayerElement%s: %d {\n Version: 101\n Name: "%s"\n MappingInformationType: "ByVertice"\n ReferenceInformationType: "Direct"\n' % (typ,idx,key)
        text += array(field,(v for row in mesh[key] for v in row)) + '}\n'
        layers.setdefault(idx,[]).append((typ,idx))
    for layer, elements in sorted(layers.items()):
        text += 'Layer: %d {\n Version: 100\n' % layer
        for typ, idx in elements:
            text += 'LayerElement: {\n Type: "LayerElement%s"\n TypedIndex: %d\n}\n' % (typ,idx)
        text += '}\n'
    text += '}\n Model: 1002, "Model::CapturedMesh", "Mesh" {\n Version: 232\n Shading: T\n Culling: "CullingOff"\n }\n}\nConnections: {\n C: "OO",1001,1002\n C: "OO",1002,0\n}\n'
    with open(path,"w",encoding="utf-8") as f:
        f.write(text)


def write_obj(path, mesh):
    """Write the same captured geometry as OBJ for UE's static-mesh importer.

    Our minimal ASCII FBX is useful as evidence, but UE's FBX importer may
    report that it contains no mesh. OBJ keeps positions, UV0 and normals.
    """
    uvs = mesh.get("uv0", [])
    normals = mesh.get("normal", [])
    count = len(mesh["position"])
    if uvs and len(uvs) != count:
        raise ValueError("UV0 count differs from position count")
    if normals and len(normals) != count:
        raise ValueError("Normal count differs from position count")
    with open(path, "w", encoding="ascii") as f:
        f.write("# Kiana captured input-assembly geometry; material roles unresolved\n")
        f.write("o CapturedMesh\n")
        for row in mesh["position"]:
            f.write("v %.9g %.9g %.9g\n" % tuple(row[:3]))
        for row in uvs:
            f.write("vt %.9g %.9g\n" % tuple(row[:2]))
        for row in normals:
            f.write("vn %.9g %.9g %.9g\n" % tuple(row[:3]))
        for tri in mesh["triangles"]:
            refs = []
            for value in tri:
                index = value + 1
                if uvs and normals:
                    refs.append("%d/%d/%d" % (index, index, index))
                elif uvs:
                    refs.append("%d/%d" % (index, index))
                elif normals:
                    refs.append("%d//%d" % (index, index))
                else:
                    refs.append(str(index))
            f.write("f %s\n" % " ".join(refs))


def export_draw(ctrl, event, parent, save_textures=True, position_name="", attribute_map=None):
    action = action_at(ctrl.GetRootActions(),event)
    if action is None or not action.flags & rd.ActionFlags.Drawcall:
        raise ValueError("Select a draw call, not a marker/copy/dispatch")
    ctrl.SetFrameEvent(event,True)
    mesh = extract_mesh(ctrl,action,position_name,attribute_map)
    os.makedirs(parent,exist_ok=True)
    output = tempfile.mkdtemp(prefix="draw_%d_" % event,dir=parent)
    path = os.path.join(output,"draw_%d.fbx" % event)
    write_fbx(path,mesh)
    obj_path = os.path.join(output,"draw_%d.obj" % event)
    write_obj(obj_path,mesh)
    manifest = {"event_id":event,"fbx":path,"obj":obj_path,"vertices":len(mesh['position']),"triangles":len(mesh['triangles']),
                "attributes":mesh['attributes'],"available_attributes":mesh['available_attributes'],
                "instance_count":int(action.numInstances),"textures":[],"warnings":mesh['warnings'],
                "notes":["Input-assembly coordinates and UVs preserved; no automatic axis flip or scale.",
                         "No original rig, shader deformation or material reconstruction.",
                         "Instanced draws export one source mesh without per-instance transforms.",
                         "Texture bindings are recorded, not guessed as albedo/normal/material channels.",
                         "Textures are PNG previews of mip 0 / slice 0; HDR precision is not preserved."]}
    if save_textures:
        textures = ctrl.GetTextures()
        descriptions = dict((str(t.resourceId),t) for t in textures)
        saved = {}
        ps = ctrl.GetPipelineState()
        for stage in (rd.ShaderStage.Vertex,rd.ShaderStage.Hull,rd.ShaderStage.Domain,
                      rd.ShaderStage.Geometry,rd.ShaderStage.Pixel,rd.ShaderStage.Compute,
                      rd.ShaderStage.Amplification,rd.ShaderStage.Mesh):
            for used in ps.GetReadOnlyResources(stage,True):
                resource = used.descriptor.resource
                key = str(resource)
                if key not in descriptions:
                    continue
                binding = {"stage":str(stage),"resource_id":key,"index":int(used.access.index),
                           "array_element":int(used.access.arrayElement)}
                if key not in saved:
                    filename = re.sub(r"[^\w.-]","_",key)+".png"
                    try:
                        desc = rd.TextureSave()
                        desc.resourceId,desc.destType,desc.mip = resource,rd.FileType.PNG,0
                        desc.slice.sliceIndex = 0
                        result = ctrl.SaveTexture(desc,os.path.join(output,filename))
                        if result != rd.ResultCode.Succeeded:
                            raise RuntimeError(str(result))
                        saved[key] = {"file":filename,"width":descriptions[key].width,"height":descriptions[key].height}
                    except Exception as e:
                        saved[key] = {"error":str(e)}
                binding.update(saved[key])
                manifest["textures"].append(binding)
    with open(os.path.join(output,"manifest.json"),"w",encoding="utf-8") as f:
        json.dump(manifest,f,indent=2,ensure_ascii=False)
    return manifest
