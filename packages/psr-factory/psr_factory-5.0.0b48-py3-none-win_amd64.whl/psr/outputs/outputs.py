# PSR Factory. Copyright (C) PSR, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import csv
import os
from pathlib import Path
from typing import (List)
import pandas
import psr.factory


_language_dict_map = {
    0: 'ENG',
    1: 'ESP',
    2: 'POR',
}

_default_language = 0


def __rename_lang_columns(df: pandas.DataFrame) -> pandas.DataFrame:
    default_language_code = _language_dict_map.get(_default_language, 'ENG')
    languages = list(_language_dict_map.values())
    languages.remove(default_language_code)
    lang_cols = [col for col in df.columns if col.startswith(tuple(languages))]
    df = df.drop(columns=lang_cols)
    # Rename the default language column to remove prefix ENG-
    for column in df.columns:
        if column.startswith(f"{default_language_code}-"):
            new_col = column[len(f"{default_language_code}-"):]
            df = df.rename(columns={column: new_col})
    return df


def get_available_outputs_by_model(tool_path: str) -> pandas.DataFrame:
    dat_file = os.path.join(tool_path, "indexdat.fmt")
    if not os.path.exists(dat_file):
        raise FileNotFoundError(f"Could not find {dat_file}")
    cls_file = os.path.join(tool_path, "indexcls.fmt")
    if not os.path.exists(cls_file):
        raise FileNotFoundError(f"Could not find {cls_file}")
    typ_file = os.path.join(tool_path, "indextyp.fmt")
    if not os.path.exists(typ_file):
        raise FileNotFoundError(f"Could not find {typ_file}")

    dat_df = pandas.read_csv(dat_file, delimiter=',', encoding='latin1', skiprows=1)
    dat_df = __rename_lang_columns(dat_df)
    dat_df.drop(columns=["PSRIO"], inplace=True)

    cls_df = pandas.read_csv(cls_file, delimiter=',', encoding='latin1', skiprows=1)
    cls_df = __rename_lang_columns(cls_df)
    cls_df.rename(columns={"Name": "ClassName"}, inplace=True)
    cls_df.drop(columns=["Description", "PSRIO-Class"], inplace=True)

    typ_df = pandas.read_csv(typ_file, delimiter=',', encoding='latin1', skiprows=1)
    typ_df = __rename_lang_columns(typ_df)
    typ_df.rename(columns={"Name": "TypeName"}, inplace=True)

    # merge class names and type names
    dat_df = dat_df.merge(cls_df, how='left', left_on='Class', right_on='!Class')
    dat_df = dat_df.merge(typ_df, how='left', left_on='Type', right_on='!Type')
    dat_df.drop(columns=["!Class", "!Type"], inplace=True)
    dat_df.rename(columns={"!Num": "Number", "TypeName": "Type", "ClassName": "Class"}, inplace=True)

    return dat_df


class AvailableOutput:
    def __init__(self):
        self.filename = ""
        self.file_type = ""
        self.description = ""
        self.unit = ""
        self.attribute_class = ""
        self.case_path = ""
    def load_dataframe(self) -> psr.factory.DataFrame:
        full_file_name = str(self)
        return psr.factory.load_dataframe(full_file_name)

    def __str__(self):
        return os.path.join(self.case_path, f"{self.filename}.{self.file_type}")

    def __repr__(self):
        return f"AvailableOutput(path='{str(self)}', description='{self.description}', unit='{self.unit}', attribute_class={self.attribute_class})"


def get_available_outputs(case_path: str) -> List[AvailableOutput]:
    indice_grf_path = os.path.join(case_path, "indice.grf")
    outputs = []
    with open(indice_grf_path, 'r', encoding='latin1') as f:
        next(f)  # Skip header
        next(f)
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            if len(row) >= 4:
                output = AvailableOutput()
                full_file_name = row[0].strip()
                output.filename, output.file_type = os.path.splitext(full_file_name)
                output.filename = output.filename.strip()
                output.file_type = output.file_type.lstrip('.').strip()
                output.description = row[1].strip()
                output.unit = row[2].strip()
                output.attribute_class = row[3].strip()
                output.case_path = case_path
                outputs.append(output)
    return outputs


class OutputsDataFrame(pandas.DataFrame):
    def __setitem__(self, key, value):
        if isinstance(value, bool):
            self.loc[key, 'Active'] = value
        else:
            super().__setitem__(key, value)
            
    def save(self, case_path: str) -> None:
        save(self, case_path)


def save(df: pandas.DataFrame, case_path: str) -> None:
    index_df = load_index_dat(case_path)

    for filename, row in df.iterrows():
        mask = index_df['Num'] == row['Num']
        if any(mask):
            index_df.loc[mask, 'YN'] = 1 if row['Active'] else 0

    output_lines = ['Num Graph...........................|...Unid Type  Y/N']
    for _, row in index_df.iterrows():
        line = f"{row['Num']:>3d} {row['Description']:<33}{row['Unit']:7} {int(row['Type']):>4d} {row['YN']:>4d}"
        output_lines.append(line)
        
    index_file = os.path.join(case_path, "index.dat")
    with open(index_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(f"{line}\n")


def load_index_dat(case_path: str) -> pandas.DataFrame:
    index_file = os.path.join(case_path, "index.dat")
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"Could not find {index_file}")
    
    widths = [4, 33, 8, 5, 4]
    names = ['Num', 'Description', 'Unit', 'Type', 'YN']
    
    return pandas.read_fwf(
        index_file,
        widths=widths,
        names=names,
        skiprows=1
    )


def load(case_path: str) -> OutputsDataFrame:
    sddp_path = Path("C:/PSR")
    sddp_dirs = [d for d in sddp_path.iterdir() if d.name.startswith("Sddp")]
    if not sddp_dirs:
        raise FileNotFoundError("Could not find SDDP installation")
    sddp_path = sorted(sddp_dirs)[-1]
            
    fmt_file = Path(sddp_path) / "Oper" / "indexdat.fmt"
    if not fmt_file.exists():
        raise FileNotFoundError(f"Could not find {fmt_file}")
        
    fmt_df = pandas.read_csv(fmt_file, delimiter=',', encoding='latin1', skiprows=1)
    index_df = load_index_dat(case_path)
    
    outputs_df = OutputsDataFrame()
    for _, row in fmt_df.iterrows():
        num = row['!Num']
        filename = row['Filename']
        index_row = index_df[index_df['Num'] == num]
        if not index_row.empty:
            outputs_df.loc[filename, 'Num'] = num
            outputs_df.loc[filename, 'Active'] = bool(index_row['YN'].iloc[0])
            
    return outputs_df