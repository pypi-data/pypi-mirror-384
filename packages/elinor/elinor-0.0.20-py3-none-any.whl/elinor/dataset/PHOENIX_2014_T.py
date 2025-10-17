# TODO:
import os
import pandas as pd
from typing import List, Generator, Optional
from elinor import count_files_by_end
from PIL import Image
# from dataclasses import dataclass
from dataclasses import dataclass
from string import Template
from tqdm import tqdm
from types import SimpleNamespace
import numpy as np

"""
TemplateFeatureDir = Template("${root_dir}/features/fullFrame-210x260px/${split}")
TemplateAnnotation = Template("${root_dir}/annotations/manual/PHOENIX-2014-T.${split}.corpus.csv")
TemplateFrame = Template("images${frame}.png")
"""
T = SimpleNamespace(
    FeatureDir = Template("${root_dir}/features/fullFrame-210x260px/${split}"),
    Annotation = Template("${root_dir}/annotations/manual/PHOENIX-2014-T.${split}.corpus.csv"),
    Frame = Template("images${frame}.png")
)


@dataclass
class BaseDatasetPhoenix2014TItem:
    frames: List[Image.Image]
    paths: List[str]
    num: int
    orth: str
    translation: str
    poses: Optional[np.ndarray]
    dirname: Optional[str]


class BaseDatasetPhoenix2014T(object):
    """Phoenix-2014-T数据集基础类

    数据集结构大致如下：
    PHOENIX-2014-T-release-v3/
    └── PHOENIX-2014-T       <------- ROOT DIR
        ├── annotations
        │   └── manual
        ├── evaluation
        │   ├── sign-recognition
        │   └── sign-translation
        ├── features
        │   └── fullFrame-210x260px
        │       ├── dev
        │       ├── test
        │       └── train
        └── models
            └── languagemodels
    """
    def __init__(
            self, 
            root_dir="./PHOENIX-2014-T",
            split="dev" # train, test, dev
        ):
        self.root_dir=root_dir
        self.features_dir = T.FeatureDir.substitute(root_dir=self.root_dir,split=split)
        self.annotations_path = T.Annotation.substitute(root_dir=self.root_dir, split=split)
        self.metadata = self.generate_metadata_from_annotations()


    def __len__(self):
        return len(self.metadata)


    def __getitem__(self, index):
        metadata = self.metadata.iloc[index]
        frames =  self.get_frames_by_dirname(metadata.dirname)
        paths = self.get_paths_by_dirname(metadata.dirname)
        num = self.metadata.iloc[index].num

        return BaseDatasetPhoenix2014TItem(
            frames=frames,
            paths=paths,
            num=num,
            orth=metadata.orth,
            translation=metadata.translation,
            dirname=metadata.dirname,
            poses=None,
        )


    def generate_metadata_from_annotations(self):
        metadata = pd.read_csv(self.annotations_path, sep="|").rename(columns={"name": "dirname"})
        
        frame_nums = []
        for dirname in tqdm(metadata.dirname):
            # Check if the directory exists
            dir_path = os.path.join(self.features_dir, dirname)
            frame_num = len([f for f in os.listdir(dir_path) if f.endswith('.png')])
            frame_nums.append(frame_num)
        
        metadata["num"] = frame_nums
        return metadata 
    

    def get_frames_by_dirname(self, dirname) -> Generator:
        video_path = os.path.join(self.features_dir, dirname)
        frame_num = self.metadata[self.metadata["dirname"] == dirname].num.item()
        frames = [""] * frame_num
        for i in range(frame_num):
            frame_path = os.path.join(video_path, T.Frame.substitute(frame=f"{i+1:04d}"))
            frames[i] = Image.open(frame_path)
        return frames


    def get_paths_by_dirname(self, dirname) -> Generator:
        video_path = os.path.join(self.features_dir, dirname)
        frame_num = self.metadata[self.metadata["dirname"] == dirname].num.item()
        paths = [""] * frame_num
        for i in range(frame_num):
            frame_path = os.path.join(video_path, T.Frame.substitute(frame=f"{i+1:04d}"))
            paths[i] = frame_path
        return paths

# TODO: 需要实现一个数据集的子类，来实现对姿态数据的处理
class AdvancedDatasetPhoenix2014T(BaseDatasetPhoenix2014T):
    def __init__(self, root_dir="./PHOENIX-2014-T", split="dev"):
        super().__init__(root_dir=root_dir, split=split)
        self.poses_dir = os.path.join(self.root_dir, "features", "pose", split)
        self.metadata = self.generate_metadata_from_annotations()
        pass