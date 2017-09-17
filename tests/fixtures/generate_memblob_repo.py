#!/usr/bin/env python3
#
# Copyright (c) 2004-present, Facebook, Inc.
# All Rights Reserved.
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import argparse
import glob
import os
import shutil


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a memblob repo rust source"
    )
    parser.add_argument("--install_dir")
    parser.add_argument("source")
    return parser.parse_args()


def chunk_string(s):
    for start in range(0, len(s), 2):
        yield s[start:start + 2]


if __name__ == '__main__':
    args = parse_args()
    shutil.copytree(args.source, os.path.join(args.install_dir, args.source))
    os.chdir(args.install_dir)
    with open(os.path.join(args.install_dir, "lib.rs"), "w") as rs:
        rs.writelines(
            """
// Copyright (c) 2004-present, Facebook, Inc.
// All Rights Reserved.
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.

extern crate memblob;
extern crate membookmarks;
extern crate mercurial_types;
extern crate memheads;
extern crate blobrepo;
extern crate blobstore;
extern crate ascii;
extern crate heads;
extern crate futures;

use memblob::Memblob;
use membookmarks::MemBookmarks;
use mercurial_types::NodeHash;
use memheads::MemHeads;
use blobrepo::BlobRepo;
use ascii::AsciiString;
use blobstore::Blobstore;
use heads::Heads;
use futures::future::Future;

pub fn getrepo() -> BlobRepo<MemHeads<NodeHash>, MemBookmarks<NodeHash>, Memblob> {
    let bookmarks: MemBookmarks<NodeHash> = MemBookmarks::new();
    let heads: MemHeads<NodeHash> = MemHeads::new();
    let blobs = Memblob::new();

"""
        )
        for head in glob.glob(os.path.join(args.source, "heads", "head-*")):
            head = head[-40:]
            rs.write(
                '    heads.add(&NodeHash::from_ascii_str(&AsciiString::from_ascii("{}").unwrap()).unwrap()).wait().expect("Head put failed");\n'.
                format(head)
            )
        rs.write("\n")
        blob_prefix_len = len(os.path.join(args.source, "blobs", "blob-"))
        for blob in glob.glob(os.path.join(args.source, "blobs", "blob-*")):
            key = blob[blob_prefix_len:]
            with open(blob, "rb") as data:
                blobdata = "\\x".join(chunk_string(data.read().hex()))
                rs.write(
                    '    blobs.put(String::from("{}"), b"\\x{}".to_vec()).wait().expect("Blob put failed");\n'.
                    format(key, blobdata)
                )
        rs.writelines("""
    BlobRepo::new(heads, bookmarks, blobs)
}
""")