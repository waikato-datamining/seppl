import json
import os
import traceback

from platformdirs import user_cache_dir
from typing import List, Optional


class ClassCache:

    def __init__(self, appname: str, super_class: str, disabled: bool = False, debug: bool = False):
        """
        Initializes the cache.

        :param appname: the name of the app this cache is for
        :type appname: str
        :param super_class: the superclass this cache is for
        :type super_class: str
        :param disabled: whether the cache is disabled
        :type disabled: bool
        :param debug: whether to have more debugging info
        :type debug: bool
        """
        self.appname = appname
        self.super_class = super_class
        self.cache_dir = user_cache_dir(appname)
        self.cache_file = os.path.join(self.cache_dir, super_class + ".json")
        self.can_cache = None
        self.disabled = disabled
        self.debug = debug
        self._cache = None

    def _initialize(self):
        """
        Initializes the cache dir, if necessary.
        """
        if self.disabled:
            return
        if not os.path.exists(self.cache_dir):
            try:
                if self.debug:
                    print("Initializing class cache dir: %s" % self.cache_dir)
                os.makedirs(self.cache_dir)
                self.can_cache = True
            except:
                print("Failed to initialize class cache dir: %s" % self.cache_dir)
                self.can_cache = False
        else:
            self.can_cache = True

    def is_cached(self) -> bool:
        """
        Checks whether the super class has been cached.

        :return: True if cached
        :rtype: bool
        """
        self._initialize()
        return not self.disabled and self.can_cache and os.path.exists(self.cache_file)

    @property
    def cache(self) -> Optional[List[str]]:
        """
        Returns the cached classes, loads them from disk, if necessary.

        :return: the cached classes, None if no cache available
        :rtype: list or None
        """
        if self.disabled:
            return None
        if self._cache is None:
            return self.load()
        else:
            return self._cache

    @cache.setter
    def cache(self, classes: List[str]):
        """
        Updates the cached classes. Automatically saves the cache.

        :param classes: the classes to update the cache with
        :type classes: list
        """
        if self.disabled:
            return
        self.save(classes)

    def reset(self) -> bool:
        """
        Resets the cache and removes any existing cache file.

        :return: True if nothing to reset or successfully deleted, False if disabled or failed to delete cache file
        :rtype: bool
        """
        self._cache = None

        if self.disabled:
            return False
        if not self.is_cached():
            return True

        try:
            if self.debug:
                print("Removing class cache for '%s' at: %s" % (self.super_class, self.cache_file))
            os.remove(self.cache_file)
            return True
        except:
            print("Failed to remove class cache for '%s' from: %s" % (self.super_class, self.cache_file))
            traceback.print_exc()
            return False

    def load(self) -> Optional[List[str]]:
        """
        Loads the cache for the super class, if possible.

        :return: the list of cached classes, None if no cache available or disabled
        :rtype: list or None
        """
        if self.disabled:
            return None
        if not self.is_cached():
            return None

        try:
            if self.debug:
                print("Loading class cache for '%s' from: %s" % (self.super_class, self.cache_file))
            with open(self.cache_file, "r") as fp:
                self._cache = list(json.load(fp))
        except:
            print("Failed to load class cache for '%s' from: %s" % (self.super_class, self.cache_file))
            traceback.print_exc()
            self._cache = None

        return self._cache

    def save(self, classes: List[str]) -> bool:
        """
        Updates the cache file, if possible.

        :param classes: the classes to store in the cache
        :type classes: list
        :return: True is cache updated successfully, False if disabled or failed to update cache file
        :rtype: bool
        """
        if self.disabled:
            return False
        self._cache = classes
        if not self.can_cache:
            return False

        try:
            if self.debug:
                print("Saving class cache for '%s' to %s: " % (self.super_class, self.cache_file))
            with open(self.cache_file, "w") as fp:
                json.dump(self._cache, fp, indent=2)
            return True
        except:
            print("Failed to save class cache for '%s' to: %s" % (self.super_class, self.cache_file))
            traceback.print_exc()
            return False
