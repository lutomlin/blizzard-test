import requests, json
from pprint import pprint

WEBAPI_ITM_URL = 'https://us.api.battle.net/wow/item/'
WEBAPI_SET_URL = 'https://us.api.battle.net/wow/item/set/'
API_KEY = 'deaqgky9sxzn4tav8urhbvdt983g9thp'

LBR = '----------------------------------------'

def itemApiReq(idx,locale='en_US',api_key=API_KEY,jsonp=''):
    '''Send an Item API request'''
    req_string = WEBAPI_ITM_URL + str(idx) + '?locale=' + str(locale) + "&apikey=" + api_key
    if jsonp:
        req_string += '&jsonp=' + str(jsonp)
    r = requests.get(req_string)
    return r
    
def itemSetApiReq(idx,locale='en_US',jsonp=''):
    '''Send an Item Set API request'''
    req_string = WEBAPI_SET_URL + str(idx) + '?locale=' + str(locale) + "&apikey=" + API_KEY
    if jsonp:
        req_string += '&jsonp=' + str(jsonp)
    r = requests.get(req_string)
    return r
    
    ###################################################################################################################
    
def test1():
    '''Test 1/f/i/2 - Compare Item and Item Set data to make sure they match up.'''
    print 'Test 1/f/i/2 - Compare Item and Item Set data to make sure they match up.'
    print LBR
    failed = False
    item_list = [76749, 76750, 76751, 76752, 76753]
    for item in item_list:
        itemdata = json.loads(itemApiReq(item).content)
        if 'itemSet' in itemdata:
            setdata = json.loads(itemSetApiReq(itemdata['itemSet']['id']).content)
            if itemdata['itemSet'] == setdata:
                print 'Success: item {} data matched'.format(item)
                print LBR
            else:
                failed = True
                print 'Failure: item {} data does not match'.format(item)
                print 'Item Set data for item {}:'.format(itemdata['name'])
                pprint(itemdata['itemSet'])
                print 'Set data:'
                pprint(setdata)
                print LBR
    return failed

    ###################################################################################################################
    
def test2():
    '''Test 1/b/i - Try an item ID that does not refer to an existing item.'''
    print 'Test 1/b/i - Try an item ID that does not refer to an existing item.'
    print LBR
    failed = False
    item = '00012'
    r = itemApiReq(item)
    content = json.loads(r.content)
    if r.status_code != 404:
        failed = True
        print 'Failure: item ID {} gives status code {} instead of 404'.format(item,r.status_code)
        print LBR
    if r.reason != 'Not Found':
        failed = True
        print 'Failure: item ID {} gives reason {} instead of "Not Found"'.format(item,r.reason)
        print LBR
    if content['reason'] != 'unable to get item information.':
        failed = True
        print 'Failure: item ID {} gives body reason {}'.format(item,content['reason'])
        print LBR
    if r.status_code == 404 and r.reason == 'Not Found' and content['reason'] == 'unable to get item information.':
        print 'Success: Invalid item ID {} gives a 404 Not Found error with the correct reason'.format(item)
        print LBR
    return failed
    
    ###################################################################################################################
    
def test3():
    '''Test 1/c/iii - Check each locale for valid returns.'''
    print 'Test 1/c/iii - Check each locale for valid returns.'
    print LBR
    failed = False
    localelist = ['en_US',
                  'es_MX',
                  'pt_BR',]
                  #'zh_TW', ### Not available on the US API
                  #'ko_KR',
                  #'en_GB',
                  #'de_DE',
                  #'es_ES',
                  #'fr_FR',
                  #'it_IT',
                  #'pl_PL',
                  #'pt_PT',
                  #'ru_RU']
    item = '76749'
    for locale in localelist:
        r = itemApiReq(item,locale=locale)
        itemdata = json.loads(r.content)
        r_cont_lang = r.headers['Content-Language']
        if r_cont_lang != locale.replace('_','-'):
            failed = True
            print 'Failure: Locale {} returns response in {}'.format(locale,r_cont_lang)
        #if itemdata['name'] ... ideally here you'd be able to check
        #the name, description etc were in the correct language.
        else:
            print 'Success: Locale {} returned response in {}'.format(locale,r_cont_lang)
        print LBR
    return failed
    
    ###################################################################################################################
    
def test4():
    '''Test 2/e/i - Check that the JSONP function wrap works correctly for Item Set API'''
    print '''Test 2/e/i - Check that the JSONP function wrap works correctly for Item Set API'''
    print LBR
    failed = False
    jsonp = 'functionName123'
    jsonplen = len(jsonp)
    item = 1060
    r_with_jsonp = itemSetApiReq(item,jsonp=jsonp).content
    r_no_jsonp = itemSetApiReq(item).content
    if r_with_jsonp[:len(jsonp)] == jsonp:
        print 'Success: JSONP function name correctly appended to front.'
        print LBR
    else:
        failed = True
        print 'Failure: JSON function name returned is {} instead of the requested {}'.format(r_with_jsonp[:len(jsonp)],jsonp)
        print LBR
    if r_with_jsonp[jsonplen] == '(' and r_with_jsonp[-2:] == ');':
        print 'Success: brackets correctly added for JSONP callback function.'
        print LBR
    else:
        failed = True
        print 'Failure: brackets not detected correctly:'
        print r_with_jsonp
        print LBR
    if r_with_jsonp[jsonplen+1:-2] == r_no_jsonp:
        print 'Success: JSON data is identical to that retrieved without the JSONP argument.'
        print LBR
    else:
        failed = True
        print 'Failure: JSON data is different for item {}:'.format(item)
        print 'With JSONP:'
        pprint(r_with_jsonp)
        print 'Without JSONP:'
        pprint(r_no_jsonp)
        print LBR
        
    return failed
    
    ###################################################################################################################
    
def test5():
    # Test should be done last to stop throttling interfering with other tests
    # I'm not happy with this test as it is - it will not pass consistently, as I cannot rate-limit the messages accurately.
    # It also requires some work to check all the X-Plan-Qps-Current values are there and in order, although that is secondary.
    '''Test 1/g/i - Test throttling feature with >100 requests/sec'''
    print '''Test 1/g/i - Test throttling feature with >100 requests/sec (using 200/sec)'''
    print LBR
    failed = False
    
    import threading, time
    item = 76749
    rs = []
    duration = 1 #test duration in seconds - was 5
    rate = 200 #messages per second
    print 'Getting comparison response'
    #This should likely repeat until it works. It will fail if we are already above our limit due to other autotests.
    comparison_r = itemApiReq(item)
    time.sleep(1)
    print 'Got comparison response'
    print LBR
    
    if comparison_r.headers['X-Plan-Qps-Allotted'] == '100':
        print 'Success: X-Plan-Qps-Allotted is 100'
    else:
        failed = True
        print 'Failure: X-Plan-Qps-Allotted is {} instead of 100'.format(comparison_r.headers['X-Plan-Qps-Allotted'])
    print LBR
    
    def collect():
        #Massively abuse GIL! This isn't a very strictly timed test.
        #print 'Sending request'
        r = itemApiReq(item)
        rs.append(r)
        #Uncomment here to watch the responses roll in with their Qps-Current number
        #print r.headers['X-Plan-Qps-Current']
        
    print 'Sending requests...'
    for i in xrange(duration * rate):
        t = threading.Thread(target=collect)
        t.start()
        #This would limit them to the right rate, but seems to slow it down too much?
        time.sleep(1.0/rate)
    print "Requests sent."
    print LBR
    
    print 'Waiting for all responses...'
    c = 0
    while True:
        time.sleep(0.1)
        c += 1
        if len(rs) == duration * rate:
            print 'All requests returned'
            print LBR
            break
        if c > 100:
            failed = True
            print 'Failure: Short-circuiting, 10 second timeout exceeded!'
            print LBR
            break
    
    if len(rs) < duration * rate:
        failed = True
        print 'Failure: Too few responses returned, missing responses'
    else:
        print 'Success: All requests obtained a response'
    print LBR
    
    #Count number of 200 vs 403 responses
    print 'Checking responses...'
    n200 = 0
    n403 = 0
    for r in rs:
        #uncomment this to see how the 'X-Plan-Qps-Current' header varies - it will go up to some number and back down to 1
        #this shows how fast the API is actually processing our messages
        #print 'X-Plan-Qps-Current: ' + r.headers['X-Plan-Qps-Current']
        if r.status_code == 200 and r.content == comparison_r.content:
            n200 += 1
        elif r.status_code == 403 and r.content != comparison_r.content:
            n403 += 1
        elif r.status_code == 200 and int(r.headers['X-Plan-Qps-Current']) > 100:
            failed = True
            print 'Failure: r.status_code 200 with current Qps > 100 - {}'.format(r.headers['X-Plan-Qps-Current'])
        elif r.status_code == 403 and int(r.headers['X-Plan-Qps-Current']) <= 100:
            failed = True
            print 'Failure: r.status_code 403 with current Qps  <= 100 - {}'.format(r.headers['X-Plan-Qps-Current'])
    print LBR
            
    if duration*rate > n200 > 100 * duration:
        #Not a failure, but not the ideal scenario.
        print 'Warning: API accepted more than 100 per second (less than max) - accepted {} items'.format(n200)
        print LBR
    elif n200 == duration*rate:
        failed = True
        #Failing here may not actually mean it is broken, just that the rate limiting does not work correctly.
        print 'Failure: API accepted all {} requests!'.format(n200)
        print LBR
    elif n200 < 100 * duration:
        failed = True
        print 'Failure: API accepted fewer than 100 per second - accepted {} items'.format(n200)
        print LBR
    elif n200 == 100 * duration:
        print 'Success: API accepted the correct number of requests ({})'.format(100*duration)
        print LBR
    if n200+n403 == duration * rate:
        pass
    else:
        failed = True
        print 'Failure: 200 + 403 not equal to total requests sent - {} responses'.format(n200+n403)
        print LBR
    
    max_current = 0
    for r in rs:
        max_current = max(max_current, int(r.headers['X-Plan-Qps-Current']))
        if r.headers['X-Plan-Qps-Current'] == '101':
            print 'Success: X-Plan-Qps-Current exceeded X-Plan-Qps-Allotted'
            print LBR
            break
    else:
        failed = True
        print 'Failure: X-Plan-Qps-Current did not max out - highest per-second requests recorded by API is {}'.format(max_current)
        print LBR
    
    #print rs
    #print len(rs)
    return failed

    ###################################################################################################################
    
if __name__ == '__main__':
    print LBR
    print 'Blizzard Senior Test Engineer interview!'
    print 'Running tests.'
    print LBR
    num_fail = 0
    num_pass = 0
    for t in (test1,test2,test3,test4,test5):
        try:
            if t():
                num_fail += 1
                print 'Test failure! {}'.format(t.__doc__)
                print LBR
            else:
                num_pass += 1
        except Exception as err:
            #This is very general, but we do want these tests to fail easily (and I'm on a limited timescale)
            num_fail += 1
            print 'Error! Test exception caught - {}'.format(err)
            print LBR
    print LBR
    print 'Tests Passed: {} // Tests Failed: {}'.format(num_pass,num_fail)
    print LBR
    print LBR