#!/usr/bin/env python

import sys
import os
import yaml

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from git import Repo, RemoteProgress

from pprint import pprint
try:
	from collections import OrderedDict
except ImportError:
	from ordereddict import OrderedDict

class RepoManager(object):
	def __init__(self):
		self.config = self.load_file(file=os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.yaml"))
		for repo_name in sorted(self.config["repos"].keys()):
			if repo_name != "misc-tools":
				continue
			logging.debug("Updating %s" % repo_name)
			repodata = self.get_repo(repo_name=repo_name)
			to_path=os.path.join(os.getcwd(),repo_name)
			if not os.path.exists(to_path):
				repo = Repo.clone_from(url=repodata["github_url"], to_path=to_path)
			else:
				repo = Repo.init(to_path)
			if not repo.remotes.origin:
				logging.debug("creating origin to %s" % repodata["github_url"])
				origin = repo.create_remote('origin', url=repodata["github_url"])
			if repo.remotes.origin.url != repodata["github_url"]:
				logging.debug("deleting origin %s" % repo.remotes.origin.url)
				repo.delete_remote(origin)
				origin = repo.create_remote('origin', url=repodata["github_url"])
			else:
				origin = repo.remotes.origin
			#logging.debug("origin.fetch")
			# origin.fetch()
			#logging.debug("origin.pull")
			#logging.debug(origin.refs[0].remote_head)
			# origin.pull()
			#origin.refs[0].remote_head)
			#logging.debug("repo.submodules")
			if repo.is_dirty() or len(repo.untracked_files):
				repo.index.add(repo.untracked_files)
				pprint(repo.active_branch)
				logging.debug("commit")
				repo.index.commit("Repo Manager Commit")
				#repo.active_branch.commit
				logging.debug("push")
				origin.push()
			for sm in repo.submodules:
				logging.debug("Updating submodule %s" % sm)
				sm.update()
			#logging.debug(repo.active_branch)

	def load_file(self, file):
		try:
			with open(file, 'r') as ymlfile:
				data = yaml.load(ymlfile)
				return data
		except:
			print "OH SNAP"
			return ""

	def get_repo(self,repo_name):
		if not repo_name in self.config["repos"].keys():
			return {}
		repo = self.config["defaults"].copy()
		repo["repo_name"] = repo_name
		dict_merge(target=repo,source=self.config["repos"][repo_name])
		return self.interpolate(data=repo, interpolate_data=repo)

	def interpolate(self, key=None, data=None, interpolate_data=None):
		val = ""
		if data is None:
			data = self.config
		if interpolate_data is None:
			interpolate_data = data

		if key is None:
			item = data
		else:
			if not key in data.keys():
				return
			item = data[key]

		kt = type(item)
		if kt in [str, int]:
			val = item
		if kt in [list]:
			val = ', '.join(map(str, item))
		if kt in [set,tuple]:
			val = item.join(", ")
		if kt in [OrderedDict, dict]:
			vals = dict()
			for skey in item.keys():
				vals[skey] = self.interpolate(key=skey,data=item,interpolate_data=interpolate_data)
			return vals
 		try:
			while (val.find('%') != -1):
				val = (val) % interpolate_data
		except:
			return val
		return val

def dict_merge(target, source, overwrite=True):
	""" Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
	updating only top-level keys, dict_merge recurses down into dicts nested
	to an arbitrary depth, updating keys. The ``source`` is merged into
	``target``.
	:param target: dict onto which the merge is executed
	:param source: dict merged into target
	:param overwrite: overwrite values in target even if the keys exist
	:return: None
	"""
	for k, v in source.iteritems():
		if (k in target and isinstance(target[k], dict)
				and isinstance(source[k], dict)):
			dict_merge(target=target[k], source=source[k])
		else:
			if not k in target.keys() or overwrite:
				target[k] = source[k]

def equal_dicts(d1, d2, ignore_keys):
	ignored = set(ignore_keys)
	for k1, v1 in d1.iteritems():
		if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
			return False
	for k2, v2 in d2.iteritems():
		if k2 not in ignored and k2 not in d1:
			return False
	return True


if __name__ == "__main__":
	mgr = RepoManager()
