"""
This module is devoted to all heuristics in finding 
installed games for better code and tests encapsulation.

The task is mainly to match specific string (registry key, directory name, ect.)
with candidate application titles that _may_ be installed with 2 things in mind in this order:
    1. avoiding false positives
    2. gives as much positive results as possible
"""

import difflib
from typing import Callable, TypeVar, Set

T = TypeVar('T', bound=str)


class TitleMatcher:
    def __init__(self, candidates: Set[str], confirm_ok_callback: Callable[[str], bool]):
        """
        :param candidates:    set of app names used for exact and close matching with directory names
        :confirm_ok_callback: tells if chosen match is OK and corresonding candidate can be removed
        """
        self.__candidates = candidates
        self.__confirm_ok_callback = confirm_ok_callback
    
    def match(self, subject, cutoff):
        word = self._prepare_word(subject)
        matches = difflib.get_close_matches(word, self.__candidates, cutoff=1)
        for candidate in matches:
            if self.__confirm_ok_callback(candidate):
                self.__candidates.remove(candidate)
                return candidate
        matches = difflib.get_close_matches(word, self.__candidates, cutoff=cutoff)


    
    def _prepare_word(self, subject):
        """Operations like removing spaces"""
        return subject
