Glossary
============

.. glossary::

    CUs
      Concurrent users or number of concurrent threads executing tests.

    Request
      A single GET/POST/redirect/xmlrpc request.

    Page 
      A request with redirects and resource links (image, css, js)
      for an html page.
    
    STPS
      Successful tests per second.

    SPPS
      Successful pages per second.

    RPS
      Requests per second, successful or not.

    maxSPPS
      Maximum SPPS during the cycle.

    maxRPS
      Maximum RPS during the cycle.

    MIN
      Minimum response time for a page or request.

    AVG
      Average response time for a page or request.

    MAX
      Maximmum response time for a page or request.

    P10
      10th percentile, response time where 10 percent of pages or requests are delivered.

    MED
      Median or 50th percentile, response time where half of pages or requests are delivered.

    P90
      90th percentile, response time where 90 percent of pages or requests are delivered.

    P95
      95th percentile, response time where 95 percent of pages or requests are delivered.

    Apdex
      Application Performance Index, this is a numerical measure of user satisfaction, it is based on three zones of application responsiveness:

      * Satisfied: The user is fully productive. This represents the time value (T seconds) below which users are not impeded by application response time.
      * Tolerating: The user notices performance lagging within responses greater than T, but continues the process.
      * Frustrated: Performance with a response time greater than 4*T seconds is unacceptable, and users may abandon the process.

      By default T is set to 1.5s this means that response time between 0 and 1.5s the user is fully productive, between 1.5 and 6s the responsivness is tolerating and above 6s the user is frustrated.

      The Apdex score converts many measurements into one number on a uniform scale of 0-to-1 (0 = no users satisfied, 1 = all users satisfied).

      To ease interpretation the Apdex score is also represented as a rating:

      * U for UNACCEPTABLE represented in gray for a score between 0 and 0.5
      * P for POOR represented in red for a score between 0.5 and 0.7
      * F for FAIR represented in yellow for a score between 0.7 and 0.85
      * G for Good represented in green for a score between 0.85 and 0.94
      * E for Excellent represented in blue for a score between 0.94 and 1

      Visit http://www.apdex.org/ for more information.

