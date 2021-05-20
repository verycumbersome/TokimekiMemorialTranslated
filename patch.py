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

import utils
import config

path = os.path.dirname(__file__)
shiftjis_table = None


def read_ptr(ptr):
    """Read ps1 pointer from file"""
    ptr = reversed([ptr[i:i + 2] for i in range(0, len(ptr), 2)])
    ptr = "".join(list(ptr))

    return ptr


def get_ptr_tables(bin_path):
    """ Get all pointers from a 'block' in ROM

    Args:
        bin_path: Path for game bin file

    Returns:
        Returns dict of pointer tables with associated data

    """

    f_ptr = os.open(os.path.join(path, bin_path), os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)

    tables = {}
    end = config.MEM_MAX

    while True:
        table_idx = mm.rfind(config.TABLE_SEP, config.MEM_MIN, end)
        if table_idx < 1:
            break

        table = mm[table_idx:end][len(config.TABLE_SEP):].hex()


        tid = table[:8]
        table = table[0x18:]

        addr = get_tbl_addrs(table)
        if addr:
            tables[tid] = addr

        end = table_idx


    # for tid in tables:
        # for ptr in tables[tid]:
            # if "0x6481" in ptr:
                # print(tables[tid][ptr])
                # print("asdf")

    # print(json.dumps(tables, indent=4))
    # print(len(tables))


def get_table_pointers(table):
    """Read a pointer table and return relative ROM and RAM address for each pointer

    Args:
        tbl: Input pointer table to parse
        rom_start: Start address for tbl position in ROM

    Returns:
        Returns dict of relative pointer addresses

    """

    # 34D91980
    print("34D91980".lower() in table.lower())

    tbl = table.replace(" ", "")

    # Make the pointer is the correct length
    if not table.find("80") > 6:
        return None

    # Iterate through table and pop the pointer from the end of the table
    # while appending each pointer to a list
    pointers = []
    while tbl.find("80") > 6:
        ptr_idx = tbl.rfind("80")
        ptr = read_ptr(tbl[ptr_idx - 6:ptr_idx + 2])
        ptr = int(ptr[2:], 16)  # Convert pointer to int

        if ptr > 0x100000: # Make sure pointer location is sufficiently large
            pointers.append({
                "hex":hex(ptr),
                "text":tbl[ptr_idx - 6:ptr_idx + 2],
                "val":ptr
            })
        tbl = tbl[:ptr_idx - 6]

    # Remove all pointers from table
    tbl = table
    for p in pointers:
        tbl = tbl.replace(p["text"], "[PTR]")

    # print(tbl)

    # TODO Fix this bytes fromhex bullshit
    # Checks to make sure that the sequence is a valid shift-jis sentence
    sentences = []
    for sentence in tbl.split("00"):
        try:
            seq = utils.decode_seq(bytes.fromhex(sentence))
            if utils.check_validity(seq) > 0.7:
                sentences.append(sentence)
        except:
            pass

    # Get sentence indices
    sentences = sorted([table.index(s) for s in sentences]) 
    text_pointers = sorted(pointers, key=lambda x: x["val"])

    best = []
    for ptr in text_pointers:
        offset = ptr["val"] - sentences[0] if sentences else 0
        ptrs = [p["val"] - offset for p in text_pointers]

        matches = [p in sentences for p in ptrs]
        best.append({"offset":offset, "matches":matches})

    if len(best) > 1:
        best = max(best, key = lambda x: sum(x["matches"]))
        text_pointers = [p["val"] - best["offset"] for p in text_pointers]


    # for t in text_pointers:


    print(text_pointers)
    print(sum(best["matches"]))



def create_shiftjis_table(filename, create_atlas=False):
    """Quick util to generate shift-jis atlas table

    Args:
        filename: Filename for the shift-jis translation rules
        create_atlas: Boolean for whether to create atlas shift-jis table

    Returns:
        Returns encoding table for shift-jis as a dict

    """

    print(shiftjis_table)
    shift_table = open(os.path.join(path, filename), "r")

    tbl = {}
    for line in tqdm.tqdm(shift_table.readlines()):
        line = line.split("#")[0].split("\t")[:2]

        left = str(line[0][2:])
        right = bytes.fromhex(left).decode("shift-jis", "ignore")

        if left and right and not any(re.findall("<|>", right, re.IGNORECASE)):
            tbl[left] = right

    if create_atlas:
        with open(os.path.join(path, "patch/Atlas.tbl"), "w") as table:
            table.write(config.TABLE_HEADER)

            for item in tbl:
                table.writelines(item + "=" + tbl[item] + "\n")

    return tbl


def parse_shift_table(filename):
    """Quick util to generate shift-jis atlas table"""
    shift_table = open(os.path.join(path, filename), "r")

    with open(os.path.join(path, "patch/game.tbl"), "w") as table:
        table.write(config.TABLE_HEADER)
        for line in tqdm.tqdm(shift_table.readlines()):
            line = line.split("#")[0].split("\t")[:2]

            left = str(line[0][2:])
            right = bytes.fromhex(left).decode("shift-jis", "ignore")

            if left and right and not any(re.findall("<|>", right, re.IGNORECASE)):
                table.writelines(left + "=" + right + "\n")


def create_atlas(bin_path, dialog_path, trans_path):
    """Create Atlas file for referencing dialog translations in ROM"""
    f_ptr = os.open(os.path.join(path, bin_path), os.O_RDWR)
    mm = mmap.mmap(f_ptr, 0, prot=mmap.PROT_READ)
    write_ptr = 0x29D3E3BE

    dialog_table = json.load(open(os.path.join(path, dialog_path), "r"))
    translation_table = json.load(open(os.path.join(path, trans_path), "r"))

    with open(os.path.join(path, "patch/Atlas.txt"), "w") as atlas_file:
        atlas_file.write(config.ATLAS_HEADER)

        for item in tqdm.tqdm(dialog_table):
            seq = dialog_table[item]["seq"]
            addr = dialog_table[item]["addr"]
            seq_size = sys.getsizeof(seq)

            # mm.seek(write_ptr)
            # mm.write(utils.encode_english("asdf"))
            write_ptr += seq_size

            print(addr[2:])
            print(hex(write_ptr)[2:])
            line_buf = f"#JMP(${addr[2:]}) // Jump to insertion point\n"
            line_buf += f"#WRITE(ptr, ${hex(write_ptr)[2:]})\n"
            # line_buf += f"{seq}\n\n"
            line_buf += "ｗｈａｔ　ｓｈｏｕｌｄ[end]\n\n"
            atlas_file.writelines(line_buf)

tbl = "095935020000080000000800000000000000000000000000000000000000000000000000eb0000000001001000000000000000000000000000000000000000000000000000000000000000000000000000000000010100001c01001100000000000000000000000000000000000000000000000000000000000000000000000000000000e8d4198000d5198018d5198030d5198048d5198060d5198078d5198090d51980a8d51980c0d51980d8d51980f0d5198008d6198020d6198038d6198050d6198068d6198080d6198098d61980b0d61980c8d61980e0d61980f8d6198010d7198028d7198040d7198058d7198070d7198088d71980a0d71980b8d71980d0d71980e8d7198000d8198018d8198030d8198048d8198060d8198078d819807cd8198080d81980acd81980bcd81980c4d81980e4d81980ecd819800cd9198082d3815b82c181422082e282c182c68b7882dd8e9e8ad482a98163814200000034d91980b4ee198082cd814182cd82a281422082a082cc81418c4e82cd816381480000005cd9198082a082c181418e84814196ec8b85959482c520837d836c815b83578383815b82f082e282c182c482a282e92093f896ec8db98af382c882f182be82af82c781420000000082c5814189b482c989bd82cc977081638148000082a082c882bd82c982cd81418daa90ab82aa82a082e982ed8142208e8482c688ea8f8f82c981418d628e71898082f02096da8e7782b582dc82b582e582a48149000000007cd91980c0d91980d4d9198088ab82a282af82c7814196ec8b8582c982cd2082a082dc82e88bbb96a182c882a282f182be81420024da198082bb82a4816381422082a082c882bd82aa978882c482ad82ea82ea82ce81412082a982c882e882cc90ed97cd82c981638142000082b282df82f182cb814182c582e082bf82e582c182c620948382a282a982d482e882b782ac82be82e681420082bb82f182c882b182c682c882a281492082c582e0816381412096b3979d8bad82a282cd82c582ab82c882a282ed82cb814200008b4382aa8cfc82a282bd82e7814188ea93788ca982c9208d7382b182a482a982c881480082a482f1814191d282c182c482e982ed81492082bb82ea82b682e1814200000050da198084da1980b0da1980e4da198008db198082a882a281418da182cc93f896ec8db98af382be82eb81480000000082a082a0814182bb82a482dd82bd82a282be82cb81420000895e93ae959482cc834183438368838b82aa81412082a8914f82c882f182a982c92089bd82cc977082be82c182bd82f182be81420000000082c882f182a981412095948a8882cc8aa9975582dd82bd82a281420082d3815b82f181422082a081418ef68bc68e6e82dc82c182bd8142003cdb198058db198070db1980a8db1980c4db198082a082c181418e84814183548362834a815b959482c520837d836c815b83578383815b82f082e282c182c482a282e92093f896ec8db98af382c882f182be82af82c781420000000082c5814189b482c989bd82cc97708163814881420000000082a082c882bd82c982cd81418daa90ab82aa82a082e982ed8142208e8482c688ea8f8f82c981418d9197a78ba38b5a8fea82f02096da8e7782b582dc82b582e582a4814900000000f4db19803cdc198054dc198088ab82a282af82c7814183548362834a815b82c982cd2082a082dc82e88bbb96a182c882a282f182be814200a8dc198089b4814196ec8b85959482c882f182be82af82c7816381420000000082a682c1816381420000000082a082f182dc82e88141208f6f82c482c882a282af82c782cb81420097fb8f4b82b582c882ab82e181418d628e71898082c9208d7382af82c882a282b682e182c882a2814200000082bb82e882e182bb82a482be814200008da1937882a982e78141905e96ca96da82c92097fb8f4b82c9978882c882b382a282e68142000000d8dc1980f4dc198000dd19801cdd198048dd198058dd198096ec8b85959482c981412082a082f182c896ba82a282bd82f182be816381420098dd198089b4814183548362834a815b95942082c882f182be82af82c78163814200000082a682c1816381420000000082a082f182dc82e88141208f6f82c482c882a282af82c782cb81420097fb8f4b82b582c882ab82e181418d9197a78ba38b5a8fea82c9208d7382af82c882a282b682e182c882a2814200000082bb82e882e182bb82a482be814200008da1937882a982e78141905e96ca96da82c92097fb8f4b82c9978882c882b382a282e68142000000bcdd1980dcdd1980e8dd198004de198034de198044de198083548362834a815b959482c981412082a082f182c896ba82a282bd82f182be816381420084de1980927882ad82c882c182bf82e182c182bd82e6814220816982f18148208ca982a982af82c882a296ba82aa82a282e982c88142816a00000000acde198082a082c1814196ec8b85959482cc95fb82c582b782a981480000000082bb82a482be82af82c78163814200008da193fa82a982e7837d836c815b83578383815b82c682b582c42093fc959482b582bd814193f896ec8db98af382c582b781422082e682eb82b582ad82a88ae882a282b582dc82b78142000082a0814189b481414681422082b182bf82e782b182bb82e682eb82b582ad81420000000082bb82ea82b682e181638142208d628e71898096da8e7782b582c481412097fb8f4b8ae692a382c182c482cb81420000e8de198004df198014df198060df198084df198082d682a5814182a082f182c896ba82aa20837d836c815b83578383815b82c982c882c182bd82f182be81422097fb8f4b82c98b438d8782aa2cd681416f3258220c4ae9a864e1d42af25125fcd0bb9ad5e5c284e2f681bf395543b7aaeae9eddb7571542cea152f88b2ee7bc684f7bd3896d68dedd034fe8776380fd5a8f932207bd64737814ee85e8d37767daf1e9bdb70ad12d269d95d75ce2037b48a85dda524151d6d920027e3c70df3f12bc441e10b51f4ff54a909de8c0cdc6719bf46b41511ab188afe84e1a7d17288519c8f98dfeebc913e9fa5f9d30e515512c3aaabadc3b2e20e53d2816535fbf3b4b7ae48525c977a7a54c1a80660aee3e1b6114f47f41da2576dc8a999b2568b96fd0c888a20e9cba47fc8fa5e30631960b689faef818b2825bf940eceeb49b4696ff38cf746ac13f5faabf4f1fd1fa3ae113e9a9b867c8c7288e18ec05eb24218e4449200"

if __name__=="__main__":
    # get_ptr_tables(os.path.join(path, "patch/Atlas.bin"))
    get_table_pointers(tbl)
    # shiftjis_table = create_shiftjis_table(os.path.join(path, "patch/shiftjis_table.txt"))

    # with open("test_table.txt", "r") as test_table_fp:
        # get_tbl_addrs(test_table_fp.read(), 0x19C804, 0x6481998)

    # create_atlas(
        # os.path.join(path, "patch/Atlas.bin"),
        # os.path.join(path, "patch/dialog_table.json"),
        # os.path.join(path, "patch/translation_table.json"),
        # )
