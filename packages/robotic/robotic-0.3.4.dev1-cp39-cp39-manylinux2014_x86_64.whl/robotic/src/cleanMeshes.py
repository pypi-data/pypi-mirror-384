#!/usr/bin/env python3

import argparse
import glob
import os
from robotic.src.mesh_helper import *

parser = argparse.ArgumentParser(
    description='Utility to clean meshes in meshes/')

parser.add_argument('-view', help='view mesh', action="store_true")
parser.add_argument('-meshlab', help='apply meshlab filters', action="store_true", default=False)

def main():
    args = parser.parse_args()

    files = sorted(glob.glob('meshes/*.h5'))

    for file in files:
        if file[-4]=='-':
            continue

        M = MeshHelper(file)
        if M.mesh is None:
            continue

        #-- repair
        print(' before repair:')
        M.report()
        M.repair(mergeTolerance=1e-4)
        # M.texture2vertexColors()
        print(' after repair:')
        print('  watertight:', M.mesh.is_watertight)
        print('  oriented:', M.mesh.is_winding_consistent)
        M.report()

        #-- export/view
        M.export_h5()
        # M.export_h5(M.filebase+'-.h5')
        if args.view:
            M.view()

        #-- meshlab processing
        if args.meshlab:
            M.export_ply('z.ply')
            print('<<< meshlab <<<')
            ret = os.system(f'meshlabserver -i z.ply -o {M.filebase}.ply -m vc -s meshlabFilters.mlx')
            print('>>> meshlab >>>')
            if not ret:
                M2 = MeshHelper(f'{M.filebase}.ply')
                # uv = M2.mesh.visual.uv
                # M2.mesh.visual = M.mesh.visual
                # M2.mesh.visual.uv = uv
                # M2.view()
                M2.export_h5(M.filebase+'.h5')
            # os.system(f'rm z.ply {M.filebase}.ply')

if __name__ == "__main__":
    main()
