import io
import tarfile
import zipfile


class Archiver:
	def __init__(self, name, compression=None):
		self.name = name

		if self.name.endswith(".tgz") or self.name.endswith(".tar.gz"):
			self.ar = tarfile.open(self.name, "w:gz")
			self.arType = "tgz"
		else:
			self.ar = zipfile.ZipFile(self.name, "w", compression=zipfile.ZIP_DEFLATED)
			self.arType = "zip"


	def addFile(self, name, data):
		if self.arType == "tgz":
			tarinfo = tarfile.TarInfo(name=name)
			tarinfo.size = len(data)
			self.ar.addfile(tarinfo, io.BytesIO(data))
		else:
			self.ar.writestr(name, data)


	def close(self):
		self.ar.close()
