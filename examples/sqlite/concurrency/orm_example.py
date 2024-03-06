#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) The University of Strathclyde 2024
# Author: Leighton Pritchard
#
# Contact:
# leighton.pritchard@strath.ac.uk
#
# Leighton Pritchard,
# Strathclyde Institute of Pharmacy and Biomedical Sciences
# University of Strathclyde
# 161 Cathedral Street
# Glasgow
# Scotland,
# G4 0RE
# UK
#
# The MIT License
#
# Copyright (c) 2024 The University of Strathclyde
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Module for manipulating an example pyani-plus SQLite3 db.

This is an SQLAlchemy-based ORM
"""

import logging
import sys

from pathlib import Path
from typing import Any

import click

from rich.logging import RichHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore

# Using the declarative system for SQLAlchemy
# We follow Flask-like naming conventions, so override some pylint errors
# Mypy doesn't like dynamic base classes
#  see https://github.com/python/mypy/issues/2477
Base = declarative_base()  # type: Any
Session = sessionmaker()  # pylint: disable=C0103

# Set up logging format
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


@click.command()
@click.option("--path", default="defaultdb", help="Path to database")
@click.option(
    "--force",
    default=False,
    is_flag=True,
    help="Set to True to overwrite existing database",
)
def createdb(path: str, force: bool) -> None:
    """Create an empty pyani SQLite3 database at the passed path.

    :param dbpath:  path to pyani database
    """
    logger = logging.getLogger()

    dbpath = Path(path)  # work with pathlib objects
    logger.info("Attempting to create sqlite3 database at %s" % dbpath)

    # If the database exists, raise an error rather than overwrite
    if dbpath.is_file():
        if not force:
            logger.error("Database %s already exists (exiting)", dbpath)
            sys.exit()
        logger.warning("Database %s already exists - overwriting", dbpath)
        dbpath.unlink()  # remove existing database

    # If the path to the database doesn't exist, create it
    if not dbpath.parent.is_dir():
        logger.info("Creating database parent directory %s", dbpath.parent)
        dbpath.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine("sqlite:///{}".format(dbpath), echo=False)
    Base.metadata.create_all(engine)
    logger.info("Created sqlite3 database at %s" % dbpath)


def get_session(dbpath: Path) -> Any:
    """Connect to an existing pyani SQLite3 database and return a session.

    :param dbpath: path to pyani database
    """
    engine = create_engine("sqlite:///{}".format(dbpath), echo=False)
    Session.configure(bind=engine)
    return Session()


# Manage command-line options with a click group
@click.group()
def group():
    pass


group.add_command(createdb)

if __name__ == "__main__":
    group()
