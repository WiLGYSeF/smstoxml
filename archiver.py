import io
import tarfile
import zipfile


class Archiver:
	def __init__(self, name, type=None, compression=None):
		self.name = name
		self.arType = type

		if self.arType not in ["tar", "tgz", "zip"]:
			if self.name.endswith(".tgz") or self.name.endswith(".tar.gz"):
				self.arType = "tgz"
			else:
				self.arType = "zip"

		if self.arType == "tgz":
			self.ar = tarfile.open(self.name, "w:gz")
		else:
			self.ar = zipfile.ZipFile(self.name, "w", compression=zipfile.ZIP_DEFLATED)


	def addFile(self, name, data):
		if self.arType == "tgz":
			tarinfo = tarfile.TarInfo(name=name)
			tarinfo.size = len(data)
			self.ar.addfile(tarinfo, io.BytesIO(data))
		else:
			self.ar.writestr(name, data)


	def close(self):
		self.ar.close()
