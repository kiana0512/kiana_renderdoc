// Build against ufbx.c / ufbx.h to independently validate generated FBX files.
#include "ufbx.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
  if(argc != 2) return 2;
  ufbx_error error;
  ufbx_scene *scene = ufbx_load_file(argv[1], NULL, &error);
  if(!scene) { fprintf(stderr, "FBX load failed: %s\n", error.description.data); return 1; }
  if(scene->meshes.count != 1) return 3;
  ufbx_mesh *mesh = scene->meshes.data[0];
  printf("vertices=%zu faces=%zu triangles=%zu normals=%d tangents=%d colors=%d uv_sets=%zu\n",
         mesh->num_vertices, mesh->num_faces, mesh->num_triangles,
         mesh->vertex_normal.exists, mesh->vertex_tangent.exists,
         mesh->vertex_color.exists, mesh->uv_sets.count);
  if(!mesh->num_vertices || !mesh->num_triangles) return 4;
  for(size_t i=0; i<mesh->num_indices; ++i)
    if(mesh->vertex_indices.data[i] >= mesh->num_vertices) return 5;
  ufbx_free_scene(scene);
  return 0;
}
