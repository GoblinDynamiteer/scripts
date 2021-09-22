#!/usr/bin/env python3

import argparse
import os
import time
from pathlib import Path
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

import util_movie
import run
from printout import pcstr, cstr


class FirefoxBrowser():
    def __init__(self, headless: bool):
        self.opts = Options()
        self.profile = FirefoxProfile()
        if headless:
            self.set_headless()
        self.disable_image_loading()
        self.set_download_options()
        self.caps = DesiredCapabilities().FIREFOX
        self.caps["pageLoadStrategy"] = "eager"  # interactive
        self.driver = webdriver.Firefox(
            self.profile, options=self.opts, capabilities=self.caps)

    def set_headless(self):
        "Sets headless mode and disables loading of images, css and flash"
        self.opts.set_headless()

    def disable_image_loading(self):
        self.profile.set_preference('permissions.default.stylesheet', 2)
        self.profile.set_preference('permissions.default.image', 2)
        self.profile.set_preference(
            'dom.ipc.plugins.enabled.libflashplayer.so', 'false')

    def set_download_options(self):
        self.profile.set_preference(
            'browser.download.folderList', 2)  # custom location
        self.profile.set_preference(
            'browser.download.manager.showWhenStarting', False)
        self.profile.set_preference('browser.download.dir', '~/Downloads')
        self.profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk', 'application/zip')
        self.profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk', 'application/x-zip-compressed')
        # TODO: application/x-rar-compressed does not seem to work, correct mime?
        self.profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk', 'application/x-rar-compressed')

    def click_by_xpath(self, xpath):
        self.driver.find_element_by_xpath(xpath).click()

    def open_url(self, url: str):
        self.driver.get(url)

    def close(self):
        self.driver.close()


class SubSceneBrowser(FirefoxBrowser):
    XP_BUTN_SAVE = r"//button[@type='submit' and contains(., 'Save changes')]"
    XP_OPT_SWE = r"//input[@value='39']"
    XP_OPT_ENG = r"//input[@value='13']"
    XP_OPT_NOHI = r"//input[@id='hi-No']"

    def __init__(self, headless):
        FirefoxBrowser.__init__(self, headless=headless)
        self.init_webpage()

    def init_webpage(self):
        self.open_url('http://www.subscene.com')
        self.driver.find_element_by_link_text("Change filter").click()
        WebDriverWait(self.driver, 3).until(
            ec.presence_of_element_located((By.XPATH, self.XP_OPT_ENG)))
        for xpath in [self.XP_OPT_SWE, self.XP_OPT_ENG, self.XP_OPT_NOHI, self.XP_BUTN_SAVE]:
            self.click_by_xpath(xpath)
        time.sleep(0.5)

    def search(self, search_string: str):
        search_form = self.driver.find_element_by_id("query")
        search_form.send_keys(search_string)
        search_form.submit()
        WebDriverWait(self.driver, 10).until(ec.title_contains(search_string))
        results = self.driver.find_elements_by_class_name('title')
        time.sleep(5)
        return [x.text for x in results]

    def get_subtitle_releases(self, language="English"):
        results = self.driver.find_elements_by_partial_link_text(language)
        return [x.text for x in results]

    def use_query_result(self, result_str):
        self.driver.find_element_by_link_text(result_str).click()
        WebDriverWait(self.driver, 3).until(
            ec.presence_of_element_located((By.CLASS_NAME, 'imdb')))

    def get_subtitle_file(self, link_name, save_as="downloaded_sub.zip"):
        self.driver.find_element_by_partial_link_text(link_name).click()
        WebDriverWait(self.driver, 3).until(
            ec.presence_of_element_located((By.ID, "downloadButton")))
        button_element = self.driver.find_element_by_id("downloadButton")
        url = button_element.get_attribute('href')
        # TODO: urllib to download file instead of relying on curl?
        run.local_command(f"curl {url} --output {save_as}", print_info=False)
        self.driver.back()


def dl_dir_files():
    dl_dir = Path.home() / "Downloads"
    return os.listdir(dl_dir)


def best_query_match(query, matches):
    year = util_movie.parse_year(query)
    name = util_movie.determine_title(query)
    exact_match_str = f"{name} ({year})"
    for match in matches:
        if exact_match_str == match:
            return match
    for match in matches:
        if match.startswith(name):
            return match
    for match in matches:
        if str(year) in match:
            return match
    return ""


def best_subtitle_match(query, subtitles):
    for subtitle_link in subtitles:
        if ARGS.query.lower() in subtitle_link.lower():
            return subtitle_link
    for subtitle_link in subtitles:
        if "bluray" in ARGS.query.lower() and "bluray" in subtitle_link.lower():
            return subtitle_link
    for subtitle_link in subtitles:
        if "web" in ARGS.query.lower() and "web" in subtitle_link.lower():
            return subtitle_link
    for subtitle_link in subtitles:
        if "bluray" in ARGS.query.lower() and "dvd" in subtitle_link.lower():
            return subtitle_link
    return ""


class YearNotSetException(Exception):
    pass


class NoSearchMatchException(Exception):
    pass


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("query")
    ARGS = PARSER.parse_args()
    ssb = None
    dl_files = dl_dir_files()
    try:
        year = util_movie.parse_year(ARGS.query)
        name = util_movie.determine_title(ARGS.query)
        if not year:
            raise YearNotSetException("Could not determine year")
        print(f"using query: {cstr(name, 154)}")
        print(f"using year:  {cstr(year, 154)}")
        pcstr("initilizing browser driver...", "orange")
        ssb = SubSceneBrowser(headless=True)
        pcstr("searching...", "orange")
        best_search_result = best_query_match(ARGS.query, ssb.search(name))
        if not best_query_match:
            raise NoSearchMatchException(
                f"Could not find any matches for {ARGS.query}")
        print(f"found match: {cstr(best_search_result, 154)}")
        ssb.use_query_result(best_search_result)
        for lang in ["Swedish", "English"]:
            subs = ssb.get_subtitle_releases(language=lang)
            if not subs:
                print(f"no {lang} subs found...")
                continue
            best_match = best_subtitle_match(ARGS.query, subs)
            if not best_match:
                pcstr(
                    f"could not find a matching subtitle link for {lang}!", "orange")
            else:
                print(
                    f"found matching subtitle link:\n  {cstr(best_match, 154)}\n",
                    f"  VS\n  {cstr(ARGS.query, 154)}")
                print(f"downloading {lang} subtitle file")
                # TODO: determine file extension..
                ssb.get_subtitle_file(
                    best_match, save_as=f"{ARGS.query}_{lang}.zip")
    except TimeoutException as e:
        pcstr("Error occured!", "red")
        print(e)
    except YearNotSetException as e:
        pcstr("Error occured!", "red")
        print(e)
    except NoSearchMatchException as e:
        pcstr("Error occured!", "red")
        print(e)
    ssb.close()
    new_files = [x for x in dl_dir_files(
    ) if x not in dl_files and x.endswith('.zip')]
    for new_file in new_files:
        print(f"downloaded: {cstr(new_file, 154)}")
