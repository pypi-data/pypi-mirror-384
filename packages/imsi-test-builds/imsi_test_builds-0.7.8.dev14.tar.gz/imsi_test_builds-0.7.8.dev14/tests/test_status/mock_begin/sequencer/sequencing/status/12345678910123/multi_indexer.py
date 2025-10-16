import pandas as pd
from pathlib import Path

directory_paths = Path('canesm').rglob('*')

# split pahts
split_paths = [str(path).split('/') for path in directory_paths]

max_depth = max(len(path) for path in split_paths)
normalized_paths = [path + [None] * (max_depth - len(path)) for path in split_paths]

df = pd.DataFrame(normalized_paths, columns=[f'Level {i}' for i in range(max_depth)])
