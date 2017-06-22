from os import getenv, environ
from time import sleep

from unittest import TestCase
from unittest.mock import patch
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


import picraftzero

from picraftzero import Joystick, Wheelbase, steering_mixer, logger
from picraftzero import PanTilt, scaled_pair



def fake_set_speed(self, speed):
    logger.info("{}".format(speed))

def fake_set_angle(self, angle):
    logger.info("{}".format(angle))

class VirtualJoystickTest(TestCase):

    driver = None
    canvas = None
    joystick0 = None
    joystick1 = None
    motors = None
    pantile = None

    IS_CI_BUILD = getenv("CI", False)

    @staticmethod
    def setUpClass():

        if VirtualJoystickTest.IS_CI_BUILD:
            username = environ["SAUCE_USERNAME"]
            access_key = environ["SAUCE_ACCESS_KEY"]
            capabilities = {}
            capabilities["browserName"] = "chrome"
            capabilities["tunnel-identifier"] = environ["TRAVIS_JOB_NUMBER"]
            capabilities["build"] = environ["TRAVIS_BUILD_NUMBER"]
            capabilities["tags"] = [environ["TRAVIS_PYTHON_VERSION"], "CI"]
            hub_url = "%s:%s@localhost:4445" % (username, access_key)
            DRIVER = webdriver.Remote(desired_capabilities=capabilities, command_executor="http://%s/wd/hub" % hub_url)
        else:
            #DRIVER = webdriver.Safari()  # see: http://elementalselenium.com/tips/69-safari
            #DRIVER = webdriver.Chrome()   # see: https://sites.google.com/a/chromium.org/chromedriver/downloads
            d = DesiredCapabilities.CHROME
            d['loggingPrefs'] = {'browser': 'ALL'}
            DRIVER = webdriver.Chrome(desired_capabilities=d)


        VirtualJoystickTest.joystick0 = Joystick(0)
        VirtualJoystickTest.motors = Wheelbase(left=0, right=1)
        VirtualJoystickTest.motors.source = steering_mixer(VirtualJoystickTest.joystick0.values)

        VirtualJoystickTest.joystick1 = Joystick(1)
        VirtualJoystickTest.pan_tilt = PanTilt(pan=0, tilt=1)
        VirtualJoystickTest.pan_tilt.source = scaled_pair(VirtualJoystickTest.joystick1.values, 180, 0, -100, 100)

        VirtualJoystickTest.driver = DRIVER
        VirtualJoystickTest.driver.implicitly_wait(10)
        VirtualJoystickTest.driver.maximize_window()
        VirtualJoystickTest.driver.get("http://localhost:8000/")
        VirtualJoystickTest.canvas = VirtualJoystickTest.driver.find_element_by_id("camera_view")

    @staticmethod
    def tearDownClass():
        logger.info("Ending")
        VirtualJoystickTest.motors.close()
        VirtualJoystickTest.joystick0.close()
        VirtualJoystickTest.joystick1.close()
        VirtualJoystickTest.driver.quit()

    def setUp(self):
        (w, h) = (VirtualJoystickTest.canvas.size['width'], VirtualJoystickTest.canvas.size['height'])
        self.j0_xc = int(w * 0.75)
        self.j0_yc = int(h * 0.50)
        self.j1_xc = int(w * 0.25)
        self.j1_yc = int(h * 0.50)

        # do some sanity checks:
        self.assertEqual(VirtualJoystickTest.canvas.location['x'], 0)
        self.assertEqual(VirtualJoystickTest.canvas.location['y'], 0)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)
        self.assertGreater(self.j0_xc, 0)
        self.assertGreater(self.j0_yc, 0)
        self.assertGreater(self.j1_xc, 0)
        self.assertGreater(self.j1_yc, 0)

        logger.info("Window size = {}".format(VirtualJoystickTest.driver.get_window_size()))
        logger.info("Canvas x, y, w, h  = {}, {}, {}".format(VirtualJoystickTest.canvas.location, w, h))
        logger.info("j0_xc, j0_yc = {}, {}".format(self.j0_xc, self.j0_yc))
        logger.info("j1_xc, j1_yc = {}, {}".format(self.j1_xc, self.j1_yc))

    def tearDown(self):
        # Show JavaScript console log
        for entry in VirtualJoystickTest.driver.get_log('browser'):
            logger.info(entry['message'])


    def move_mouse(self, o_x, o_y, x, y):
        # force the return to center (-x, -y), doesn't want to play otherwise
        ActionChains(VirtualJoystickTest.driver) \
            .move_to_element_with_offset(VirtualJoystickTest.canvas, o_x, o_y)\
            .click_and_hold()\
            .move_by_offset(x, y)\
            .move_by_offset(-x, -y)\
            .release()\
            .perform()


    @patch.object(picraftzero.providers.get_motor_provider(), 'set_speed', fake_set_speed)
    def _test_move_joystick0(self):
        self.move_mouse(self.j0_xc, self.j0_yc, 0, -50)
        sleep(0.5)


    @patch.object(picraftzero.providers.get_servo_provider(), 'set_angle', fake_set_angle)
    def test_move_joystick1(self):
        self.move_mouse(self.j1_xc, self.j1_yc, 0, -100)
        sleep(0.5)