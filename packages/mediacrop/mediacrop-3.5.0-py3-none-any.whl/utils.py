#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


def get_file_info(filepath):
    """Get comprehensive file information"""
    try:
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'name': os.path.basename(filepath),
            'extension': os.path.splitext(filepath)[1].lower(),
            'absolute_path': os.path.abspath(filepath)
        }
    except Exception:
        return None