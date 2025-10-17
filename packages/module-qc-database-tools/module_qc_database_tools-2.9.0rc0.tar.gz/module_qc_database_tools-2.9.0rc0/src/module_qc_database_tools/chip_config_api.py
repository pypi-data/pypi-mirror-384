from __future__ import annotations

import hashlib
import io
import logging
import pickle
from datetime import datetime, timezone

import gridfs
from bson.objectid import ObjectId
from jsondiff import diff
from module_qc_data_tools.utils import get_chip_type_from_config

log = logging.getLogger(__name__)


class ChipConfigAPI:
    """
    A class representing a JSON configuration stored in MongoDB, with revision history.
    """

    def __init__(self, mongo_client, dbname="localdb"):
        """
        Initializes a new MongoDBConfig object for the given configuration ID.
        """
        self.client = mongo_client
        self.database = getattr(self.client, dbname)

    def create_config(self, serial_number, stage, branch="default"):
        """
        Create the config record for the serial number + stage on a given branch.
        """
        config_data = {"serialNumber": serial_number, "stage": stage, "branch": branch}
        record = self.database.fe_configs.find_one(config_data)
        if self.database.fe_configs.find_one(config_data) is None:
            result = self.database.fe_configs.insert_one(config_data)
            return str(result.inserted_id)

        log.info("info: config for %s already exists.", config_data)
        return str(record.get("_id"))

    def get_info(self, config_id):
        """
        Get information about the config id.
        """
        return self.database.fe_configs.find_one({"_id": ObjectId(config_id)})

    def info(self, config_id):
        """
        Like get_info but logs more.
        """
        log.info("config id = %s", config_id)

        config = self.database.fe_configs.find_one({"_id": ObjectId(config_id)})
        log.info("  - Serial Number: %s", config.get("serialNumber"))
        log.info("  - Stage: %s", config.get("stage"))
        log.info("  - Branch: %s", config.get("branch"))
        log.info("  - HEAD: %s", config.get("current_revision_id"))

    def copy_config(self, original_id, serial_number, stage, branch="default"):
        """
        Copy the config over with a new serial number, stage, and branch.
        """
        original = self.database.fe_configs.find_one({"_id": ObjectId(original_id)})
        if original is None:
            log.info("copy_config: original config was not found")
            return None

        config_data = {
            "serialNumber": serial_number,
            "stage": stage,
            "branch": branch,
            "current_revision_id": original.get("current_revision_id"),
        }
        result = self.database.fe_configs.insert_one(config_data)

        log.info(
            "copied a config from original (%s, %s, %s) to (%s, %s, %s)",
            original.get("serialNumber"),
            original.get("stage"),
            original.get("branch"),
            serial_number,
            stage,
            branch,
        )

        return str(result.inserted_id)

    def checkout(self, serial_number, stage, branch="default"):
        """
        Get the config id for the serial number, stage, and branch.
        """
        result = self.database.fe_configs.find_one(
            {"serialNumber": serial_number, "stage": stage, "branch": branch}
        )
        if result is None:
            return None
        return str(result["_id"])

    def branch(self, parent_id, new_branch, revision_id=None):
        """
        Create a new branch from a parent id.
        """
        revision_id = revision_id or self.get_revision_id(parent_id, "HEAD")

        revision = self.database.fe_config_revision.find_one(
            {"_id": ObjectId(revision_id)}
        )
        if not revision:
            msg = "Could not find a revision"
            raise ValueError(msg)

        parent = self.database.fe_configs.find_one({"_id": ObjectId(parent_id)})

        branch_content = {
            "serialNumber": parent.get("serialNumber"),
            "stage": parent.get("stage"),
            "branch": new_branch,
            "current_revision_id": ObjectId(revision_id),
        }

        branch = self.database.fe_configs.insert_one(branch_content)
        return str(branch.inserted_id)

    def get_config(self, config_id, revision=None, add_pixel_cfg=False):
        """
        Gets the JSON configuration for this object, optionally at a specific revision.
        If no revision is specified, gets the latest revision.
        """

        revision_history = self.get_revision_history(config_id)

        if revision is None:
            revision = str(
                self.database.fe_configs.find_one({"_id": ObjectId(config_id)}).get(
                    "current_revision_id"
                )
            )

        if revision not in revision_history:
            return None

        revision_doc = self.database.fe_config_revision.find_one(
            {"_id": ObjectId(revision)}
        )
        config_data = revision_doc.get("config_data")

        if add_pixel_cfg is True and revision_doc.get("pix_config") is not None:
            pixcfg_id = revision_doc.get("pix_config").get("_id")

            filesystem = gridfs.GridFS(self.client.localdb)

            data = filesystem.get(pixcfg_id).read()

            pixcfg = pickle.load(io.BytesIO(data))

            config_data.get(get_chip_type_from_config(config_data)).update(
                {"PixelConfig": pixcfg}
            )

        return config_data

    def commit(self, config_id, fe_cfg, message=""):
        """
        Commit the config for a given commit_id with some message.
        """
        pixelcfg = fe_cfg.get(get_chip_type_from_config(fe_cfg)).get("PixelConfig")

        keys_to_remove = []

        is_pixelcfg_revised = None

        if pixelcfg is not None:
            log.info("pickling pixelcfg...")
            binary = pickle.dumps(pixelcfg)

            keys_to_remove = [
                var
                for var, contents in fe_cfg.get(
                    get_chip_type_from_config(fe_cfg)
                ).items()
                if var not in ["GlobalConfig", "Parameter"]
            ]

            filesystem = gridfs.GridFS(self.client.localdb)

            md5 = hashlib.md5(binary).hexdigest()

            log.info("pixelcfg md5 hash = %s", md5)

            if self.client.localdb.fs.files.find_one({"md5": md5}) is not None:
                log.info(
                    "info: identified the same pixel config data in gridfs, reusing it."
                )
                pixelcfg_doc = self.client.localdb.fs.files.find_one({"md5": md5})
                is_pixelcfg_revised = False
            else:
                pixelcfg_id = filesystem.put(binary)
                pixelcfg_doc = self.client.localdb.fs.files.find_one(
                    {"_id": ObjectId(pixelcfg_id)}
                )
                is_pixelcfg_revised = True

        else:
            log.info("pixelcfg is None, skipping pickling")
            pixelcfg_doc = None
            is_pixelcfg_revised = True

        _ = [
            fe_cfg.get(get_chip_type_from_config(fe_cfg)).pop(key)
            for key in keys_to_remove
        ]

        config = self.database.fe_configs.find_one({"_id": ObjectId(config_id)})
        previous_revision_id = config.get("current_revision_id")

        # Compute the diff between the previous and new configuration
        if previous_revision_id is None:
            the_diff = fe_cfg
        else:
            previous_revision = self.database.fe_config_revision.find_one(
                {"_id": previous_revision_id}
            )
            if not previous_revision:
                log.error(
                    "Corrupted!! Previous revision ID %s is present for config %s but the object is not recorded in database",
                    previous_revision_id,
                    config_id,
                )
                return None

            previous_data = previous_revision.get("config_data", {})
            the_diff = diff(previous_data, fe_cfg, dump=True)

        timestamp = datetime.now(timezone.utc)

        # If no change in config, do not commit and return the previous revision_id
        if the_diff == "{}" and is_pixelcfg_revised is False:
            log.info("Nothing to commit (identical config as previous)")
            return previous_revision_id

        # Save the revision and update the config to point to it
        revision_doc = {
            "parent_revision_id": previous_revision_id,
            "config_data": fe_cfg,
            "diff": the_diff,
            "pix_config": pixelcfg_doc,
            "message": message,
            "timestamp": timestamp,
            "tags": [],
        }

        result = self.database.fe_config_revision.insert_one(revision_doc)
        revision_id = result.inserted_id
        self.database.fe_configs.update_one(
            {"_id": ObjectId(config_id)}, {"$set": {"current_revision_id": revision_id}}
        )

        log.info(
            "new commit: %s --> %s | %s | %s",
            revision_id,
            config.get("serialNumber"),
            config.get("stage"),
            config.get("branch"),
        )

        return str(revision_id)

    def _get_prev_commit(self, revision_id) -> ObjectId | None:
        revision = self.database.fe_config_revision.find_one(
            {"_id": ObjectId(revision_id)}
        )
        return revision.get("parent_revision_id") if revision else None

    def get_revision_id(self, config_id, tag="HEAD"):
        """
        Get the revision id for the config id and tag.
        """
        config = self.database.fe_configs.find_one({"_id": ObjectId(config_id)})
        revision_id = config.get("current_revision_id")
        assert revision_id, (
            f"Current revision id is missing for {config_id}. This entry is corrupted."
        )

        if tag == "HEAD":
            pass
        else:
            tag_parts = tag.split("^")
            if len(tag_parts) > 1:
                parent_num = int(tag_parts[1])
                for _i in range(parent_num):
                    revision_id = self._get_prev_commit(revision_id)

        return str(revision_id) if revision_id else None

    def get_revision_history(self, config_id):
        """
        Gets the revision history for this object.
        """
        config = self.database.fe_configs.find_one({"_id": ObjectId(config_id)})

        revision = config.get("current_revision_id")
        if revision is None:
            return []

        revision_history = [revision]

        while True:
            revision_id = self._get_prev_commit(revision_history[-1])

            if revision_id is None:
                break

            revision_history += [revision_id]

        return list(map(str, revision_history))

    def get_log(self, config_id, depth=10):
        """
        Get the log for a config id.
        """
        self.info(config_id)

        history = self.get_revision_history(config_id)

        log.info("--------------------------------------")
        for index, revision_id in enumerate(history):
            if index >= depth:
                break
            revision = self.database.fe_config_revision.find_one(
                {"_id": ObjectId(revision_id)}
            )
            tags_str = (
                ""
                if len(revision.get("tags")) == 0
                else ", (tags: " + revision.get("tags") + ")"
            )
            is_head = " (HEAD)" if index == 0 else ""
            log.info(
                "commit %s:%s %s %s",
                revision_id,
                is_head,
                tags_str,
                revision.get("message"),
            )
        log.info("--------------------------------------")
