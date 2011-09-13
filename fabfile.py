#!/usr/bin/env python

from __future__ import with_statement
from fabric.api import *
from fabric.decorators import *
from fabric.contrib import project

import glob
import logging
import os
import re
import sys

class LazyAttributeDictionary(dict):
  def __getattr__(self, key):
    if self.has_key(key):
      return self.__getitem__(key)
    else:
      raise AttributeError(key)
  def __setattr__(self, key, value):
    self.__setitem__(key, value)
  def __getitem__(self, key):
    val = super(LazyAttributeDictionary, self).__getitem__(key)
    if hasattr(val, '__call__'):
      val = val()
      self.__setitem__(key, val)
    return val

env.user = 'deploy'
opt = LazyAttributeDictionary(env)
opt.prefix = (lambda: os.path.join('/u/apps/kyototycoon', re.findall('(?:[0-9]+\.)*[0-9]+', opt.archive)[0]))
opt.target = os.path.realpath('./target')
## kyotocabinet
opt.kc_archive = (lambda: glob.glob('kyotocabinet-*.tar.gz')[-1])
opt.kc_extracted = (lambda: os.path.splitext(os.path.splitext(opt.kc_archive)[0])[0])
opt.kc_patches = (lambda: opt.kc_extracted + '.patches')
## kyototycon
opt.archive = (lambda: glob.glob('kyototycoon-*.tar.gz')[-1])
opt.extracted = (lambda: os.path.splitext(os.path.splitext(opt.archive)[0])[0])
opt.patches = (lambda: opt.extracted + '.patches')

@task
def setup():
  clean()
  build()
  upload()
  symlink()

@task
@runs_once
def clean():
  local("""
    rm -rf %(kc_extracted)s %(extracted)s %(target)s
  """ % opt)

@task
@runs_once
def build():
  build_kyotocabinet()
  build_kyototycoon()

@task
def build_kyotocabinet():
  local("""
    test -f %(kc_archive)s && ( rm -rf %(kc_extracted)s; tar zxf %(kc_archive)s )
  """ % opt)
  with lcd(opt.kc_extracted):
## patch
    local("""
      if test -d %(kc_patches)s; then
        umask 022; env QUILT_PATCHES=%(kc_patches)s quilt push -a
      fi
    """ % opt)
## configure
    local("""
      umask 022; ./configure --prefix=%(prefix)s
    """ % opt)
## build/test/install
    local("""
      umask 022; make -j4 && make -j4 check && make -j4 DESTDIR=%(target)s install
    """ % opt)

@task
def build_kyototycoon():
  local("""
    test -f %(archive)s && ( rm -rf %(extracted)s; tar zxf %(archive)s )
  """ % opt)
  with lcd(opt.extracted):
## patch
    local("""
      if test -d %(patches)s; then
        umask 022; env QUILT_PATCHES=%(patches)s quilt push -a
      fi
    """ % opt)
## configure
    local("""
      umask 022; ./configure --prefix=%(prefix)s --with-kc=%(kc)s
    """ % dict(prefix=opt.prefix, kc=os.path.realpath(opt.target + os.path.sep + opt.prefix)))
## build/test/install
    local("""
      umask 022; make -j4 && make -j4 check && make -j4 DESTDIR=%(target)s install
    """ % opt)

@task
def upload():
  run("""
    test -d %(prefix)s || mkdir -p %(prefix)s
  """ % opt)
  local_dir = os.path.realpath(opt.target + os.path.sep + opt.prefix) + os.path.sep
  project.rsync_project(local_dir=local_dir, remote_dir=opt.prefix, delete=True, extra_opts='--chmod=Du+rwx,Dgo+rx,Fu+rw,Fgo+r --links')

@task
def symlink():
  run("""
    current=`dirname %(prefix)s`/current; rm -f $current; ln -s %(prefix)s $current
  """ % opt)

# vim:set ft=python :
