#!/usr/bin/env python3

import readline
import hashlib
import signal
import json
import sys
import os


# subset of https://spdx.org/licenses/
valid_licenses = ["", "CC0-1.0"]
valid_languages = ["", "dutch", "english", "french", "german"]

# Only works on *nix systems
def rlinput(prompt, prefill=""):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try:
		return input(prompt)
	finally:
		readline.set_startup_hook()

def check_duplicate_images(db_images, images_set):
	def hash_file(path):
		with open(path, "rb") as file:
			hasher = hashlib.sha1()
			hasher.update(file.read())
			return hasher.hexdigest()

	duplicates_found = False
	hashes = {}
	for image in images_set:
		file_hash = hash_file("images/{}".format(image))
		if file_hash in hashes:
			other_image = hashes[file_hash]
			print("Files identical: 'images/{}' and 'images/{}'".format(image, other_image))

			if image in db_images:
				if other_image in db_images:
					print(" Both already in database. :/")
				else:
					print(" Remove: {}".format(other_image))
			else:
				if other_image in db_images:
					print(" Remove: {}".format(image))
				else:
					print(" Both are not in database. Remove one of them.")

			duplicates_found = True

	return duplicates_found

def get_defaults_entry(db, image):
	name, ext = os.path.splitext(image)
	for key in db:
		# match entry with different file extensions
		if key.startswith(name) and key[len(name)] == ".":
			return db[key]
	return {}

def is_valid_author(author):
	return True

def is_valid_title(author):
	return True

def is_valid_tags(tags):
	if len(tags) == 0:
		print("Tags are required!")
		return False
	if tags.lower() != tags:
		print("Only lower case letters please.")
		return False
	return True

def is_valid_license(license):
	if license not in valid_licenses:
		print("Valid licenses: {}".format(valid_licenses))
		return False
	return True

def is_valid_language(language):
	if language not in valid_languages:
		print("Valid languages: {}".format(valid_languages))
		return False
	return True

def add_image(i, n, db, image):
	print("[{}/{}] 'images/{}'".format(i, n, image))

	def get_value(prompt, is_valid, prefill=""):
		value = rlinput(prompt, prefill)
		while not is_valid(value):
			value = rlinput(prompt, value)
		return value.strip()

	def split_ext(image):
		i = image.rfind('.')
		if i == -1:
			return (image, "")
		else:
			return (image[:i], image[i+1:])

	name, ext = split_ext(image)

	if len(ext) == 0:
		print("File has no extension => ignore")
		return 0

	# image name exists
	if name in db:
		obj = db[name]
		answer = get_value("Image exists as different type {}. Add {} as new type? [Y/n] ".format(obj["exts"], ext),
			lambda v: v in ["", "Y", "n"], "")
		if answer == "" or answer == "Y":
			obj["exts"].append(ext)
			print("done")
			return 1
		else:
			print("ignore")
			return 0

	default = get_defaults_entry(db, image)

	tags = default.get("tags", "")
	title = default.get("title", "")
	author = default.get("author", "")
	license = default.get("license", "")
	language = default.get("language", "")

	while True:
		tags = get_value("Tags: ", is_valid_tags, tags)
		title = get_value("Title: ", is_valid_title, title)
		author = get_value("Author: ", is_valid_author, author)
		license = get_value("License: ", is_valid_license, license)
		language = get_value("Language: ", is_valid_language, language)

		answer = get_value("Done? [Y, n]: ", lambda v: v in ["", "Y", "n"], "")
		if answer == "" or answer == "Y":
			break

	obj = {"tags": tags, "exts": [ext]}

	if len(title) > 0:
		obj["title"] = title
	if len(language) > 0:
		obj["language"] = language
	if len(author) > 0:
		obj["author"] = author
	if len(license) > 0:
		obj["license"] = license

	db[name] = obj

	print("done")

	return 1

def main():
	def get_database():
		with open("data.json") as file:
			return json.load(file)

	def get_image_set():
		images = set()
		for filename in os.listdir("images/"):
			images.add(filename)
		return images

	def get_db_set(db):
		images = set()
		for name, obj in db.items():
			for ext in obj["exts"]:
				images.add("{}.{}".format(name, ext))
		return images

	# Exit Ctrl+C gracefully
	signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

	db = get_database()
	images = get_image_set()

	db_images = get_db_set(db)
	new_images = images - db_images

	if check_duplicate_images(db_images, images):
		print("Please remove duplicate files first!")
		return

	if len(new_images) == 0:
		print("Read {} entries, no new images => abort".format(len(db_images)))
		return

	answer = input("Start to add {} new images [Y, n]? ".format(len(new_images)))
	if answer == "n":
		return

	old_image_count = len(db_images)
	new_image_count = 0
	for i, image in enumerate(new_images):
		new_image_count += add_image(i + 1, len(new_images), db, image)

	# write anyway, this will format manual edits to data.json
	with open("data.json", "w") as outfile:
		json.dump(db, outfile, indent="  ", sort_keys=True)
		print("Wrote {} new entries to data.json => done".format(new_image_count))

if __name__ == "__main__":
	main()
