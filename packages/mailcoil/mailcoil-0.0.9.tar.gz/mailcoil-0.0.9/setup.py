import setuptools

with open("README.md") as f:
	long_description = f.read()

setuptools.setup(
	name = "mailcoil",
	packages = setuptools.find_packages(),
	version = "0.0.9",
	license = "gpl-3.0",
	description = "Effortless, featureful SMTP",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	author = "Johannes Bauer",
	author_email = "joe@johannes-bauer.com",
	url = "https://github.com/johndoe31415/mailcoil",
	download_url = "https://github.com/johndoe31415/mailcoil/archive/v0.0.9.tar.gz",
	keywords = [ "mail", "email", "smtp", "encrypted", "cms", "smime" ],
	install_requires = [
	],
	entry_points = {
		"console_scripts": [
			"mailcoil = mailcoil.__main__:main"
		]
	},
	include_package_data = False,
	classifiers = [
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3 :: Only",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"Programming Language :: Python :: 3.13",
	],
)
