import logging
import threading
from abc import ABC
from time import sleep

import allure

from zapp.driver import BROWSER, DRIVER_IMPL
from zapp.driver.selenium.factory import SeleniumBrowserFactory
from zapp.driver.playwright.factory import PlaywrightBrowserFactory

from zapp.driver import (
    BROWSER_HEIGHT,
    BROWSER_WIDTH,
    BROWSER_LIFECYCLE,
    BROWSER_GO_TO_HOST_ON_START,
    BROWSER_DISABLE_FOR_TAGS,
    REMOTE_BROWSER_PING_ENABLED,
    REMOTE_BROWSER_PING_TIMEOUT_IN_SEC,
    REMOTE_EXECUTOR,
)

log = logging.getLogger("browser_lifecycle")


class BrowserLifecycle(ABC):
    __lock = threading.Lock()

    def before_all(self, context):
        self._start_ping_thread(context)
        self._browser_factory = {
            "SELENIUM": SeleniumBrowserFactory,
            "PLAYWRIGHT": PlaywrightBrowserFactory,
        }[DRIVER_IMPL](context)

    def before_feature(self, context):
        pass

    def before_scenario(self, context):
        pass

    def after_scenario(self, context):
        pass

    def after_feature(self, context):
        pass

    def after_all(self, context):
        pass

    def is_browser_created(self, context) -> bool:
        return hasattr(context, "browser")

    def on_fail(self, context):
        if self.is_browser_created(context):
            allure.attach(
                context.browser.screenshot(),
                name="screenshot",
                attachment_type=allure.attachment_type.PNG,
            )

            allure.attach(
                context.browser.page_source(),
                name="page-source",
                attachment_type=allure.attachment_type.HTML,
            )

    def _start(self, context):
        if not hasattr(context, "tags") or not (
            set(BROWSER_DISABLE_FOR_TAGS.split(",")) & set(context.tags)
        ):
            log.info("Запуск браузера...")
            log.debug(f"TEMPDIR: {context.tempdir}")

            context.browser = self._browser_factory.create(BROWSER)

            if BROWSER_WIDTH and BROWSER_HEIGHT:
                context.browser.set_window_size(BROWSER_WIDTH, BROWSER_HEIGHT)
            if BROWSER_GO_TO_HOST_ON_START:
                context.browser.open(context.host)

    def _stop(self, context):
        with self.__lock:
            if self.is_browser_created(context):
                log.info("Завершение работы браузера...")
                context.browser.quit()
                delattr(context, "browser")

    def _register_cleanup(self, context):
        """Регистрируем cleanup вместо использования хука after:
        Отработает самым последним (после пользовательских): LIFO
        См. https://github.com/behave/behave/blob/main/features/runner.context_cleanup.feature
        """
        context.add_cleanup(self._stop, context)

    def _start_ping_thread(self, context):
        if REMOTE_EXECUTOR and REMOTE_BROWSER_PING_ENABLED:
            ping_thread = threading.Thread(
                target=self.__ping_driver, args=(context,), daemon=True
            )
            ping_thread.start()
            log.info(
                f"Запущен deamon-поток для опроса Selenoid Session раз в {REMOTE_BROWSER_PING_TIMEOUT_IN_SEC} секунд"
            )

    def __ping_driver(self, context):
        while True:
            with self.__lock:
                if self.is_browser_created(context):
                    try:
                        log.debug("[Deamon] Ping driver...")
                        _ = context.browser.title()
                    except Exception as ex:
                        log.error("[Deamon] Ping driver error: " + str(ex))
            sleep(REMOTE_BROWSER_PING_TIMEOUT_IN_SEC.total_seconds())


class EachScenarioBrowserLifecycle(BrowserLifecycle):

    def before_scenario(self, context):
        super()._start(context)
        super()._register_cleanup(context)


class EachFeatureBrowserLifecycle(BrowserLifecycle):

    def before_feature(self, context):
        super()._start(context)
        super()._register_cleanup(context)


class OneInstanceBrowserLifecycle(BrowserLifecycle):

    def before_all(self, context):
        super().before_all(context)
        super()._start(context)
        super()._register_cleanup(context)


browser_lifecycle: BrowserLifecycle = {
    "ONE_INSTANCE": OneInstanceBrowserLifecycle,
    "EACH_FEATURE": EachFeatureBrowserLifecycle,
    "EACH_SCENARIO": EachScenarioBrowserLifecycle,
}[BROWSER_LIFECYCLE]()
