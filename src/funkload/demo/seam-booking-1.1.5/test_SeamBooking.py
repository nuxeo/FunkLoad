# -*- coding: iso-8859-15 -*-
"""seam_booking FunkLoad test

$Id$
"""
import unittest
import random
from funkload.FunkLoadTestCase import FunkLoadTestCase
from webunit.utility import Upload
from funkload.utils import Data
from funkload.Lipsum import Lipsum


class SeamBooking(FunkLoadTestCase):
    """Simple test to register a new user and book an hotel.

    This test use a configuration file SeamBooking.conf.
    """

    jsf_tag_tree = '<input type="hidden" name="jsf_tree_64" id="jsf_tree_64" value="'
    jsf_tag_state = '<input type="hidden" name="jsf_state_64" id="jsf_state_64" value="'

    hotel_names = ["Tower", "Ritz", "Sea", "Hotel"]
    nb_letters = 3        # number of letter to type when searching an hotel
    password = "password" # password used for users

    def jsfParams(self, params):
        """Helper to extarct jsf states from the last page and add them to the params."""
        html = self.getBody()
        tag = self.jsf_tag_tree
        start = html.find(tag) + len(tag)
        end = html.find('"', start)
        if start < 0 or end < 0:
            raise ValueError('No Jsf STATE TREE found in the previous page.')
        state = html[start:end]
        params.insert(0, ["jsf_tree_64", state])
        tag = self.jsf_tag_state
        start = html.find(tag) + len(tag)
        end = html.find('"', start)
        if start < 0 or end < 0:
            raise ValueError('No Jsf STATE STATE found in the previous page.')
        state = html[start:end]
        params.insert(1, ["jsf_state_64", state])
        return params


    def setUp(self):
        """Setting up test."""
        self.logd("setUp")
        self.server_url = self.conf_get('main', 'url')
        self.lipsum = Lipsum()


    def test_seam_booking(self):
        # The description should be set in the configuration file
        server_url = self.server_url

        self.get(server_url + "/seam-booking/home.seam",
            description="Booking home page")
        register_link = self.listHref(content_pattern="Register New User")
        self.assert_(len(register_link), "Register link not found")
        register_link = register_link[0]

        self.get(server_url + register_link,
                 description="Register new User")
        self.assert_("register_SUBMIT" in self.getBody(),
                     "Failing to view Registration page.")

        username = self.lipsum.getUniqWord()
        realname = username + " " + self.lipsum.getUniqWord()
        password = self.password

        self.post(server_url + "/seam-booking/register.seam", self.jsfParams(params=[
            ['register:username', username],
            ['register:name', realname],
            ['register:password', password],
            ['register:verify', password],
            ['register:register', 'Register'],
            ['register_SUBMIT', '1'],
            ['register:_link_hidden_', ''],
            ['jsf_viewid', '/register.xhtml']]),
            description="Submit register form")
        self.assert_("Successfully registered as" in self.getBody(),
                     "Failing register new user.")
        params = self.jsfParams(params=[
            ['login:username', username],
            ['login:password', password],
            ['login:login', 'Account Login'],
            ['login_SUBMIT', '1'],
            ['login:_link_hidden_', ''],
            ['jsf_viewid', '/home.xhtml']])
        self.post(server_url + "/seam-booking/home.seam", params,
            description="Submit account login")
        self.assert_(username in self.getBody(),
                     "Failing login new user %s:%s" % (username, password) + str(params))
        self.assert_("No Bookings Found" in self.getBody(),
                     "Weird there should be no booking for new user %s:%s" %
                     (username, password))

        # Simulate ajax search for an hotel by typing nb_letters
        nb_letters = self.nb_letters
        hotel_query = random.choice(self.hotel_names)
        for i in range(1, nb_letters + 1):
            self.post(server_url + "/seam-booking/main.seam", self.jsfParams(params=[
            ['AJAXREQUEST', '_viewRoot'],
            ['main:searchString', hotel_query[:i]],
            ['main:pageSize', '10'],
            ['main_SUBMIT', '1'],
            ['jsf_viewid', '/main.xhtml'],
            ['main:findHotels', 'main:findHotels']]),
            description="Ajax search %i letter" % i)
            self.assert_("View Hotel" in self.getBody(),
                         "No match for search hotel.")

        # Extract the list of link to hotel and choose a random one
        hotel_links = self.listHref(content_pattern="View Hotel")
        self.get(server_url + random.choice(hotel_links),
                 description="View a random hotel in the result list")
        self.assert_("hotel_SUBMIT" in self.getBody())

        self.post(server_url + "/seam-booking/hotel.seam", self.jsfParams(params=[
            ['hotel:bookHotel', 'Book Hotel'],
            ['hotel_SUBMIT', '1'],
            ['hotel:_link_hidden_', ''],
            ['jsf_viewid', '/hotel.xhtml']]),
            description="Book hotel")
        self.assert_("booking_SUBMIT" in self.getBody())

        self.post(server_url + "/seam-booking/book.seam", self.jsfParams(params=[
            ['booking:checkinDate', '11/07/2008'],
            ['booking:checkoutDate', '11/08/2008'],
            ['booking:beds', '1'],
            ['booking:smoking', 'false'],
            ['booking:creditCard', '1234567890123456'],
            ['booking:creditCardName', realname],
            ['booking:creditCardExpiryMonth', '1'],
            ['booking:creditCardExpiryYear', '2009'],
            ['booking:proceed', 'Proceed'],
            ['booking_SUBMIT', '1'],
            ['booking:_link_hidden_', ''],
            ['jsf_viewid', '/book.xhtml']]),
            description="Proceed booking")
        self.assert_("confirm_SUBMIT" in self.getBody())

        self.post(server_url + "/seam-booking/confirm.seam", self.jsfParams(params=[
            ['confirm:confirm', 'Confirm'],
            ['confirm_SUBMIT', '1'],
            ['confirm:_link_hidden_', ''],
            ['jsf_viewid', '/confirm.xhtml']]),
            description="Confirm booking")
        self.assert_("No Bookings Found" not in self.getBody(),
                     "Booking is not taken in account.")

        # Logout
        logout_link = self.listHref(content_pattern="Logout")
        self.assert_(len(logout_link), "Logout link not found")
        logout_link = logout_link[0]
        self.get(server_url + logout_link,
            description="Logout")
        self.assert_("login_SUBMIT" in self.getBody())

        # end of test -----------------------------------------------

    def tearDown(self):
        """Setting up test."""
        self.logd("tearDown.\n")


if __name__ in ('main', '__main__'):
    unittest.main()
