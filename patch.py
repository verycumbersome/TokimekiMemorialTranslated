#!/usr/bin/env python3
"""
All ROM utils for patching the translations back into the game
"""

import os
import re
import sys
import json


import tqdm
import mmap

from halo import Halo

import pandas as pd

import utils
import config

path = os.path.dirname(__file__)


# Define globals
f_ptr = os.open(os.path.join(path, config.BIN_PATH), os.O_RDWR)
mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)


class Block:
    def __init__(self, tid, table, address, block_num):
        self.tid = tid
        self.table = table
        self.address = address
        self.block_num = block_num

        # Initialize class vars
        self.seqs = []
        self.pointers = []
        self.is_empty = True

        # Call init functions
        self.get_table_pointers()
        if len(self.pointers) > 40:
            self.get_seqs()

        else:
            return

        if len(self.seqs):
            self.is_empty = False
            self.create_ptr_table()



    def __str__(self):
        out = "\n" * 10 + "Block ID: " + self.tid + "----------------"
        out += "Block num: " + str(self.block_num) + "----------------"
        out += "POINTERS: " + json.dumps(self.pointers, indent=4)
        return out



    def get_table_pointers(self):
        tbl = self.table.replace(" ", "")

        # Make the pointer is the correct length
        if not tbl.find("80") > 6:
            return None

        # Iterate through table and pop the pointer from the end of the table
        # while appending each pointer to a list
        while tbl.find("80") > 6:
            ptr_idx = tbl.rfind("80")
            ptr = utils.read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])
            ptr = int(ptr[2:], 16)  # Convert pointer to int

            if ptr > 0x100000: # Make sure pointer location is sufficiently large
                self.pointers.append({
                    "hex":hex(ptr),
                    "text":tbl[ptr_idx - 6:ptr_idx + 2],
                    "idx":ptr
                })
            tbl = tbl[:ptr_idx - 6]


    def get_seqs(self):
        # Checks to make sure that the sequence is a valid shift-jis sentence
        for s in self.table.split("00"):
            try:
                seq = utils.decode_seq(bytes.fromhex(s))
                if utils.check_validity(seq) > 0.7 and len(seq) > 1:
                    self.seqs.append(s)
            except:
                pass

        # Get sentence indices and sort 
        self.seqs = [(self.table.index(s), s) for s in self.seqs]
        self.seqs = pd.DataFrame(self.seqs, columns = ["idx", "seqs"])
        self.seqs = self.seqs.sort_values("idx")

        # Get pointers and sort by relative pointer pos in table
        self.pointers = sorted(self.pointers, key=lambda x: x["idx"])


        # Find best offset to match max amount of pointers to sequences 
        best = []
        for ptr in tqdm.tqdm(self.pointers, leave = False):
            offset = 0
            if not self.seqs.empty:
                offset = ptr["idx"] - self.seqs["idx"][0]

            ptrs = [p["idx"] - offset for p in self.pointers]
            matches = [p in self.seqs["idx"] for p in ptrs]

            best.append({"offset":offset, "matches":matches})

        if len(best) > 2:
            best = max(best, key = lambda x: sum(x["matches"]))
            for i in range(len(self.pointers)):
                self.pointers[i]["idx"] -= best["offset"]


    def create_ptr_table(self):
        #TODO refactor
        for i, p in enumerate(self.pointers):
            p["addr"] = hex(self.address + p["idx"]) # Address in ROM that pointer points to given offset

            if p["idx"] >= 0 and p["idx"] < len(self.table):
                for s in self.seqs:
                    if s[0] == p["idx"]:
                        p["seq"] = s[0]
                        p["decoded"] = bytes.fromhex(s[1]).decode("shift-jis", "ignore")

                self.pointers[i] = p


def init_blocks():
    """ Get all pointers from a 'block' in ROM

    Args:
        bin_path: Path for game bin file

    Returns:
        Returns dict of pointer tables with associated data

    """
    spinner = Halo(text='Creating block table', spinner='dots')

    blocks = {}
    block_num = 0
    end = config.MEM_MAX
    chunk_table = ""


    x="D3815B82C1814194E682EA82BD814220816992A9918182AD919682E982CC82CD8141208B438E9D82BF82AA82A282A282C882A08142816A000000008CCC198082A882CD82E682A481420000CCCC1980816381492082A8814182A882CD82E682A4814220816993E982EA93E982EA82B582A2937A82BE82C882A08142816A00008C4E82E08DA18141919682C182C482AB82BD82CC8148000082A082A0814182BB82A482BE82E68142208C4E82E082BB82A482C882CC8148008E848141968892A98254824F834C838D82CC20838D815B8368838F815B834E82F0208C8782A982B582BD82B182C682C882A282A982E781420000000082DC8141968892A981418254824F834C838D".lower()

    # spinner.start()
    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)

        if table_idx < 1: # Stop parsing at end of bin file
            break

        table = mm[table_idx:end - 560][len(config.TABLE_SEP):].hex()

        tid = table[:8] # Get id
        table = table[24:] # Remove table header info 
        tmp = Block(tid, table, table_idx, block_num)

        chunk_table += table # Add each table in contiguous memory

        if tmp.is_empty:
            block_num += 1
            b = Block(tid, chunk_table, table_idx, block_num)

            if x in chunk_table:
                print("ADFDSAFAFAD")
                exit()

            if len(b.pointers) > 40:
                print(len(b.pointers))
                blocks[block_num] = b
                print(chunk_table)

            chunk_table = ""
            # print(blocks[block_num])
            # print()

        end = table_idx

    # spinner.stop()

    return blocks


def qualify_block(block):
    for p in block.pointers:
        addr = int(p["addr"][2:], 16)

        # seq = mm.find(b"\x00", addr)

        # print(p)
        print(mm[addr:addr + 40])

# def solve_blocks(blocks):
    # # for b in blocks:
    # for p in blocks[1].pointers:
        # print(p)

# def create_atlas(bin_path, dialog_path, trans_path):
    # """Create Atlas file for referencing dialog translations in ROM"""
    # f_ptr = os.open(os.path.join(path, bin_path), os.O_RDWR)
    # mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)
    # write_ptr = 0x29D3E3BE

    # dialog_table = json.load(open(os.path.join(path, dialog_path), "r"))
    # translation_table = json.load(open(os.path.join(path, trans_path), "r"))

    # with open(os.path.join(path, "patch/atlas.txt"), "w") as atlas_file:
        # atlas_file.write(config.atlas_header)

        # for item in tqdm.tqdm(dialog_table):
            # seq = dialog_table[item]["seq"]
            # addr = dialog_table[item]["addr"]
            # seq_size = sys.getsizeof(seq)

            # # mm.seek(write_ptr)
            # # mm.write(utils.encode_english("asdf"))
            # write_ptr += seq_size

            # print(addr[2:])
            # print(hex(write_ptr)[2:])
            # line_buf = f"#JMP(${addr[2:]}) // Jump to insertion point\n"
            # line_buf += f"#WRITE(ptr, ${hex(write_ptr)[2:]})\n"
            # # line_buf += f"{seq}\n\n"
            # line_buf += "ｗｈａｔ　ｓｈｏｕｌｄ[end]\n\n"
            # atlas_file.writelines(line_buf)

tbl="09593302000008000000080082C18149204782C182C48141208CC38EAE82E482A982E882B382F1814800000082BB82A4814182C582B782AF82EA82C782E081638142209053939682BD82E882CD81412082B282B482A282DC82B782A98148000082CD82A0816381482082C882F182C582B582E582A481480089B482AA81414782CC8370815B83678369815B81422096BC914F82CD814146814200000082BB82EA82CD81418EB897E782F082A282BD82B582DC82B582BD81422082BB82EA82C582CD81418DA193FA82CD2082E682EB82B582AD82A88AE882A282A282BD82B582DC82B781420000000082B182BF82E782B182BB81420000000024C7198040C7198098C71980ACC71980FCC7198020C81980ACEE198054C819806CC8198090C81980DCC8198034C5198040C5198054C5198078C61980D0C619801CC71980ECC81980060100FF07FF000001FF00000001000100010001FF00000000FF00000001FF000001000100010001000100FF34C9198038C919803CC9198040C919804CC9198050C9198054C919800000000000000000000000000000000000000000000000000000000009000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000A0000000E000002000000000000000000000000000000000000000000000000000000000000000000000000000000000F0000001D000003000000000000000000000000000000000000000000000000000000000000000000000000000000001E0000003000000400000000000000000000000000000000000000000000000000000000000000000000000000000000310000004700000500000000000000000000000000000000000000000000000000000000000000000000000000000000480000005F0000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001030000010000000000000000000000000000000000000000000000000000000000000000000000000000000060000000810000070000000000000000000000000000000000000000000000000000000000000000000000000000000082000000A500000800000000000000000000000000000000000000000000000000000000000000000000000000000000A6000000BB00000900000000000000000000000000000000000000000000000000000000000000000000000000000000BC000000C500000A00000000000000000000000000000000000000000000000000000000000000000000000000000000C6000000E000000B000000000000000000000000000000000000000000000000000000000000000000000000000000007CC9198094C91980ACC91980C4C91980DCC91980F4C919800CCA198024CA19803CCA198054CA19806CCA198084CA19809CCA1980B4CA1980CCCA1980E4CA1980FCCA198014CB19802CCB198044CB19805CCB198074CB19808CCB1980A4CB1980BCCB1980D4CB1980ECCB198004CC198010CC198014CC198018CC198038CC19803CCC198044CC198082D3815B82C1814194E682EA82BD814220816992A9918182AD919682E982CC82CD8141208B438E9D82BF82AA82A282A282C882A08142816A000000008CCC198082A882CD82E682A481420000CCCC1980816381492082A8814182A882CD82E682A4814220816993E982EA93E982EA82B582A2937A82BE82C882A08142816A00008C4E82E08DA18141919682C182C482AB82BD82CC8148000082A082A0814182BB82A482BE82E68142208C4E82E082BB82A482C882CC8148008E848141968892A98254824F834C838D82CC20838D815B8368838F815B834E82F0208C8782A982B582BD82B182C682C882A282A982E781420000000082DC8141968892A981418254824F834C838D8149208C4E8163814182AB82E782DF82AB8D828D5A82CC906C814800000082A482F1814182BB82A48142208E84814190B490EC965D8142208C4E82E082BB82A482C882CC81480000000082BB82A4814189B481414681422090B490EC82C182C4816381422082A082CC81419085896A959482CC90B490EC82B382F181480082BB82A482BE82AF82C7816381422082D682A581638142208E8482CC8E968141926D82C182C482E982F182BE81420000926D82C182C482E982E089BD82E081412092B4974C96BC906C82B682E182C882A282A9814200000092B48D828D5A8B8982CC8F9783588343837D815B82BE82E681422082E082C182C6814196B38D9C82C896BA82BE82C6208E7682C182C482BD82AF82C7816381420000000092B4974C96BC82CB816381422082BB82EA82E682E882E082B38141208DA19378814188EA8F8F82C9919682EB82A482E681420000DCCC19800CCD198024CD198044CD198080CD1980B0CD1980DCCD198010CE198040CE198068CE1980ACCE198082CD82CD82CD816381422090B490EC82B382F182CC91AB8EE882DC82C682A282C92082C882E782C882AB82E182A282A282AF82C782CB81420000000082CD82CD82CD82CD814182C882E782C882A282C182C481422082B682E182A08E84814182E082A482D082C682C1919682E82082B582C482AD82E982A982E781420000000089B482CD814182E082A48FAD82B58B7882F182C582A282AD82E681420000000082B182CC83578385815B8358814120975D82C182BD82A982E782A082B082E981422082B682E182A0814200000CCF198048CF19808CCF1980ACCF1980816381422082F182AE82F182AE82F182AE816381422083760CCED378A2276E0404A31C9AFF40BD7D393B60736DCD99E33271BB7D7149BABE657C8C2C78C2D134BDCD1B175D5EC0A738B2196244ADF34333957CDDDAE4A5C2ED473348FF007A3C1835C46759D0BE37DFDF9EFBAB0977AA0A476B537BA1327A01C2FE7F270BEDCDC6FE57F12784C139FAC4DF37C0B42C564C0942DB8FFFF30939C73026858C7D5B6F58DD0F4E01E25A5A0F3F5E535BE2EA671AA09FD4264C47731A4084B0AE938354C1ADD243AA6BA07BCBDC0EC2BA488283AA1F344E2F4076F2832F6328694BED3F73843C12CC58F8BF166A08FFC8489AB7B5E1C17D82642C9FEB42581DA5934DD55372C9BB2ED82828F246FE9295CC5A2EEDE6535B0B46D4D91AAE80BD275E3E113F056706BCE980103FC57C7AAE6FDC00"

if __name__=="__main__":
    blocks = init_blocks()
    # solve_blocks(blocks)

    # with open("test_table.txt", "r") as test_table_fp:
        # tbl = test_table_fp.read()

    # tid = tbl[:8]
    # b = Block(tid, tbl, 0x648198C, 1)

    # qualify_block(b)

    # shiftjis_table = create_shiftjis_table(os.path.join(path, "patch/shiftjis_table.txt"))


    # create_atlas(
        # os.path.join(path, "patch/Atlas.bin"),
        # os.path.join(path, "patch/dialog_table.json"),
