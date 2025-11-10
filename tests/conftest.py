import sys
import pathlib

# La carpeta raíz del proyecto (donde está 'app/')
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
