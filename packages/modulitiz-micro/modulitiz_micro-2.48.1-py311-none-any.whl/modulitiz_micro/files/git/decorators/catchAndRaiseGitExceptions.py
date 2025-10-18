from functools import wraps

from git import GitCommandError

from modulitiz_micro.files.git.exceptions.ExceptionGit import ExceptionGit


def catchAndRaiseGitExceptions(funzione):
	"""
	Cattura tutte le eccezioni git di vario tipo e rilancia un'eccezione custom
	"""
	
	@wraps(funzione)
	def wrapped(*args,**kwargs):
		try:
			return funzione(*args,**kwargs)
		except (GitCommandError,) as ex:
			raise ExceptionGit() from ex
	return wrapped
