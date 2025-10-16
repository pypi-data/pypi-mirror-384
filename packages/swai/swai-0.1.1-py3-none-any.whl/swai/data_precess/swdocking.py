#!/usr/bin/env python3
"""
转换格式:PDB -> PDBQT
适用于受体是pdb格式,直接转换成pdbqt
自动清理非标准残基和多构象问题
"""

import os
from pathlib import Path
from swai.utils.log import logger
from swai.data_precess.base_preprocess import BasePreprocess

# 标准的20种氨基酸残基
STANDARD_RESIDUES = {
    'ALA', 'ARG', 'ASN', 'ASP', 'CYS',
    'GLN', 'GLU', 'GLY', 'HIS', 'ILE',
    'LEU', 'LYS', 'MET', 'PHE', 'PRO',
    'SER', 'THR', 'TRP', 'TYR', 'VAL'
}

# ==================== 配置参数区域 ====================

# 输入目录（包含PDB文件的目录）
RECEPTOR_INPUT_DIR = "/mnt/nvme/shaobt/projects/sw/swai/swai/data_precess/swdocking_data_process-master/receptor"

# 输出目录（转换后的PDBQT文件存放目录）
OUTPUT_DIR = "./receptor_output"


# ====================================================

class SWDockingReceptor:
    def __init__(self, input_dir, output_dir, auto_clean_pdb=True):
        self.receptor_input_dir = input_dir
        self.output_dir = output_dir
        self.auto_clean_pdb = auto_clean_pdb

    def clean_pdb_file(self, input_file, output_file):
        """
        清理PDB文件:
        1. 如果存在多个MODEL(NMR结构),只保留第一个MODEL
        2. 去掉非标准氨基酸残基,只保留标准氨基酸的ATOM记录
        3. 移除多构象和HETATM
        事先进行该处理能避免很多由于数据问题导致的报错
        """
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        atom_count = 0
        removed_count = 0
        in_first_model = False
        has_model = False
        model_count = 0
        
        for line in lines:
            # 检测MODEL标记
            if line.startswith('MODEL'):
                model_count += 1
                has_model = True
                if model_count == 1:
                    in_first_model = True
                    # 不保存MODEL行,直接开始处理原子
                    continue
                else:
                    # 遇到第二个MODEL,停止处理
                    break
            
            # 检测ENDMDL标记
            if line.startswith('ENDMDL'):
                if in_first_model:
                    # 第一个MODEL结束,不保存ENDMDL行
                    in_first_model = False
                    break
                continue
            
            # 如果有MODEL结构但还没进入第一个MODEL,跳过
            if has_model and not in_first_model and model_count == 0:
                # 保留头部信息
                if line.startswith(('HEADER', 'TITLE', 'COMPND', 'SOURCE', 'REMARK', 'CRYST1', 'KEYWDS', 'EXPDTA', 'NUMMDL', 'AUTHOR')):
                    cleaned_lines.append(line)
                continue
            
            # 保留头部信息(无MODEL结构的情况)
            if not has_model and line.startswith(('HEADER', 'TITLE', 'COMPND', 'SOURCE', 'REMARK', 'CRYST1')):
                cleaned_lines.append(line)
                continue
            
            # 只处理ATOM记录
            if line.startswith('ATOM'):
                # 检查是否为标准氨基酸
                residue_name = line[17:20].strip()
                
                if residue_name not in STANDARD_RESIDUES:
                    removed_count += 1
                    continue
                
                cleaned_lines.append(line)
                atom_count += 1
            
            # 保留TER和END
            elif line.startswith(('TER', 'END')):
                cleaned_lines.append(line)
        
        # 确保以END结束
        if not any(line.startswith('END') for line in cleaned_lines[-5:]):
            cleaned_lines.append('END\n')
        
        # 写入清理后的文件
        with open(output_file, 'w') as f:
            f.writelines(cleaned_lines)
        
        return atom_count, removed_count

    def convert_pdb_to_pdbqt(self):
        """
        将目录下所有PDB文件转换为PDBQT格式
        
        参数:
            receptor_input_dir: 输入目录
            output_dir: 输出目录
            auto_clean: 是否自动清理PDB文件
        """
        input_path = Path(self.receptor_input_dir)
        output_path = Path(self.output_dir)
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 如果需要自动清理，创建临时目录
        if self.auto_clean_pdb:
            temp_dir = output_path / "temp_cleaned"
            temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有PDB文件
        pdb_files = list(input_path.glob("*.pdb")) + list(input_path.glob("*.PDB"))
        
        if not pdb_files:
            logger.error(f"错误: 在 {self.receptor_input_dir} 中未找到PDB文件")
            exit(1)
        
        logger.info(f"找到 {len(pdb_files)} 个PDB文件\n")
        
        success = 0
        failed = 0
        
        # 遍历转换每个文件
        for idx, pdb_file in enumerate(pdb_files, 1):
            logger.info(f"[{idx}/{len(pdb_files)}] 处理: {pdb_file.name}")
            
            try:
                # 确定使用的PDB文件
                if self.auto_clean_pdb:
                    # 清理PDB文件
                    cleaned_pdb = temp_dir / pdb_file.name
                    atom_count, removed_count = self.clean_pdb_file(pdb_file, cleaned_pdb)
                    logger.info(f"  清理完成: 保留 {atom_count} 个原子")
                    if removed_count > 0:
                        logger.info(f"  移除了 {removed_count} 个非标准残基原子")
                    pdb_to_convert = cleaned_pdb
                else:
                    pdb_to_convert = pdb_file
                
                # 输出文件
                pdbqt_file = output_path / f"{pdb_file.stem}.pdbqt"
                
                # 构建命令
                cmd = f"prepare_receptor4 -r {pdb_to_convert} -o {pdbqt_file} -A hydrogens -e True -U nphs_lps_waters_nonstdres"
                
                result = os.system(cmd + " > /dev/null 2>&1")
                
                if result == 0 and pdbqt_file.exists():
                    success += 1
                    # 获取文件大小
                    size_kb = pdbqt_file.stat().st_size / 1024
                    logger.info(f" ✓ 成功 ({size_kb:.1f} KB)\n")
                else:
                    failed += 1
                    logger.info(f" ✗ 失败\n")
            
            except Exception as e:
                failed += 1
                logger.error(f"  ✗ 异常: {str(e)}\n")
                
        # 清理临时文件和目录
        if self.auto_clean_pdb:
            try:
                for temp_file in temp_dir.glob("*.pdb"):
                    temp_file.unlink()
                temp_dir.rmdir()
            except:
                pass
        
        logger.info("="*60)
        logger.info(f"转换完成: 成功 {success} 个，失败 {failed} 个")


class SWDockingLigand:
    def __init__(self, input_dir, output_dir, input_format, extra_args=""):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.input_format = input_format
        self.extra_args = extra_args

    def convert_to_pdbqt(self):
        """
        将目录下所有指定格式文件转换为PDBQT格式(通过PDB中间格式)
        
        参数:
            input_dir: 输入目录
            output_dir: 输出目录
            input_format: 输入文件格式（如 sdf, mol2, mol)
            extra_args: 传给prepare_ligand4.py的额外参数,例如 "-A hydrogens -U nphs_lps",受体会进行加氢去水，配体一般不加
        """
        input_path = Path(self.input_dir)
        output_path = Path(self.output_dir)
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有指定格式的文件
        input_files = list(input_path.glob(f"*.{self.input_format.lower()}")) + \
                    list(input_path.glob(f"*.{self.input_format.upper()}"))
        
        if not input_files:
            logger.error(f"错误: 在 {self.input_dir} 中未找到 {self.input_format} 文件")
            exit(1)
        
        logger.info(f"找到 {len(input_files)} 个 {self.input_format} 文件")
        
        success = 0
        failed = 0
        
        # 遍历转换每个文件
        for input_file in input_files:
            base_name = input_file.stem
            temp_pdb = output_path / f"{base_name}_temp.pdb"
            pdbqt_file = output_path / f"{base_name}.pdbqt"
            
            logger.info(f"转换: {input_file.name} -> {pdbqt_file.name}")
            
            # 第一步: 使用OpenBabel转换为PDB，显式指定输入格式
            cmd1 = f"obabel -i{self.input_format.lower()} {input_file} -opdb -O {temp_pdb}"
            result = os.system(cmd1)
            
            if result != 0 or not temp_pdb.exists():
                logger.error(f"  ✗ OpenBabel转换失败")
                failed += 1
                continue
            
            # 第二步: 使用AutoDock Tools转换为PDBQT
            cmd2 = f"prepare_ligand4 -l {temp_pdb} -o {pdbqt_file}"
            if self.extra_args:
                cmd2 += f" {self.extra_args}"
            
            result = os.system(cmd2)
            
            # 删除临时PDB文件
            if temp_pdb.exists():
                temp_pdb.unlink()
            
            if result == 0 and pdbqt_file.exists():
                success += 1
                logger.info(f"  ✓ 成功")
            else:
                failed += 1
                logger.error(f"  ✗ AutoDock Tools转换失败")
        
        logger.info(f"\n转换完成: 成功 {success} 个，失败 {failed} 个")


class SWDocking(BasePreprocess):
    def __init__(self, receptor_input_dir, ligand_input_dir, output_dir, ligand_input_format="mol2"):
        self.receptor_input_dir = receptor_input_dir
        self.ligand_input_dir = ligand_input_dir

        if not os.path.exists(receptor_input_dir):
            logger.error(f"receptor_input_dir {receptor_input_dir} not exists")
            exit(1)
        if not os.path.exists(ligand_input_dir):
            logger.error(f"ligand_input_dir {ligand_input_dir} not exists")
            exit(1)
        self.output_dir = os.path.abspath(output_dir)
        self.receptor_output_dir = os.path.join(self.output_dir, "receptor_pdbqt")
        self.ligand_output_dir = os.path.join(self.output_dir, "ligand_pdbqt")
        self.receptor_worker = SWDockingReceptor(receptor_input_dir, self.receptor_output_dir, auto_clean_pdb=True)
        self.ligand_worker = SWDockingLigand(ligand_input_dir, self.ligand_output_dir, ligand_input_format)

    def process(self):
        self.receptor_worker.convert_pdb_to_pdbqt()
        self.ligand_worker.convert_to_pdbqt()
        zip_path = self.pack(self.output_dir)
        return zip_path

# if __name__ == "__main__":
#     # 输入目录（包含配体文件的目录）
#     LIGAND_INPUT_DIR = "/mnt/nvme/shaobt/projects/sw/swai/swai/data_precess/swdocking_data_process-master/ligand"

#     # 输出目录（转换后的PDBQT文件存放目录）
#     OUTPUT_DIR = "./ligand_output"

#     # 输入文件格式（sdf, mol2, mol 等）
#     INPUT_FORMAT = "mol2"

#     print("="*60)
#     print("配体格式转换工具 (SDF/MOL2/MOL -> PDB -> PDBQT)")
#     print("="*60)
#     print(f"输入目录: {LIGAND_INPUT_DIR}")
#     print(f"输出目录: {OUTPUT_DIR}")
#     print(f"输入格式: {INPUT_FORMAT}")
#     print("="*60)
#     print()
    
#     swdocking = SWDockingLigand(LIGAND_INPUT_DIR, OUTPUT_DIR, INPUT_FORMAT)
#     swdocking.convert_to_pdbqt()
