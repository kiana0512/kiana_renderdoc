import renderdoc as rd
from pathlib import Path
save = rd.TextureSave()
Path('F:/KianaStudioElectron/docs/frame38112-texture-save-api.txt').write_text(
    'mip '+str(save.mip)+' slice '+str(save.slice)+' DDS '+str(rd.FileType.DDS)+'\n'+
    str([x for x in dir(save) if not x.startswith('_')]), encoding='utf-8')
