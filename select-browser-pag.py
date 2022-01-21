from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from browsermobproxy import Server
from time import sleep, localtime, strftime
from apscheduler.schedulers.blocking import BlockingScheduler
from os import getcwd


# 开启proxy
mypath = getcwd()  # 获取当前工作目录路径,否则browsermobproxy报错
server = Server(r'{}\browsermob-proxy-2.1.4\bin\browsermob-proxy'.format(mypath))
server.start()
proxy = server.create_proxy()


## 初始化设置
chrome_options = Options()
chrome_options.add_argument('--proxy-server={0}'.format(proxy.proxy))
chrome_options.add_argument('--incognito')
chrome_options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])  # 忽略无用的日志  # 防止弹出usb设备有问题的一大串提示

# 安装驱动
browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
print("驱动已安装")


print("选课小助手")
print("菜鸡小高，在线求star★★★★★★★")
print("如果有用，抽两分钟在github点个星星呗")
print("源代码已上传至Github:https://github.com/nobodyXX/nobadyXX")
print("教程or报错看这里:")
print()
name = input("请输入学号/手机号/NetID:")
password = input("请输入密码:")


# browser = webdriver.Chrome(chrome_options=chrome_options, executable_path='chromedriver.exe')
browser.set_window_size(1920, 1080)
browser.get("http://xkfw.xjtu.edu.cn/")
print("浏览器已启动")

proxy.new_har("jieguo", options={'captureHeaders': True, 'captureContent': True})


## 获取分析选课结果
def panduan(result):
    global tip
    for entry in result['log']['entries'][-1:]:
        res_url = entry['request']['url']
        if "volunteer.do" in res_url:
            response = entry['response']
            content = response['content']['text']
            tip = content.split(',')[2].split(':')[1]
            print(tip)
            break


# 全局变量，太懒，不想传参
global SearchList, num, course, courseForSearch, tip


## 登录
browser.implicitly_wait(10)
sleep(0.5)
browser.find_element_by_name("username").send_keys(name)  # 输入账户密码
browser.find_element_by_name("pwd").send_keys(password)
browser.find_element_by_xpath('//*[@id="account_login"]').click()  # 登录按钮
sleep(1)
print("登录成功")

try:  # 本科生选课
    browser.find_element_by_xpath(
        '/html/body/div[4]/div[2]/div[1]/div/div[1]/table/tbody/tr[2]/td[1]/div/input').click()
    browser.find_element_by_xpath('//*[@id="buttons"]/button[2]').click()
except:
    print("出问题了")

sleep(1)
try:
    browser.find_element_by_xpath('//*[@id="courseBtn"]').click()  # 开始选课
except:
    sleep(2)


n = 0  # 尝试次数
tip = ""  # 选课结果通知
CourseType = ["主修推荐课程", "方案内跨年级课程", "方案外课程", "基础通识类", "主修课程（体育）", "辅修课程"]
CourseTypeId = ["aRecommendCourse", "aProgramCourse", "aUnProgramCourse", "aPublicCourse", "aSportCourse"]
SearchList = ["recommendSearch", "programSearch", "unProgramSearch", "publicSearch", "sportSearch"]


print("请输入课程板块对应的序号")
for i in range(len(CourseType)):
    print(i + 1, ":", CourseType[i])
num = int(input("请输入课程板块对应的序号:")) - 1

sleep(2)
browser.find_element_by_xpath('//*[@id="{}"]'.format(CourseTypeId[num])).click()  # 课程板块

## 课程号
course = input("请输入课程编号:")
courseForSearch = course.split('[')[0]
classid = input("有些课程如太极有多个班,请输入班级号(如02)，如果没有则按回车:")
course = course + classid


def search():
    global SearchList, num, courseForSearch
    browser.find_element_by_xpath('//*[@id="{}"]'.format(SearchList[num])).clear()  # 清空搜索框
    browser.find_element_by_xpath('//*[@id="{}"]'.format(SearchList[num])).send_keys(courseForSearch, Keys.ENTER)  # 搜索


sleep(0.5)


## 选修课
def publish():
    search()
    sleep(0.5)
    browser.find_element_by_xpath(
        "//*[contains(@tcid,'{}')and contains(text(),'选择')]".format(course.replace('[', '').replace(']', ''))).click()
    sleep(1)
    browser.find_element_by_xpath("//*[@class='cv-sure cvBtnFlag']").click()  # 确认按钮
    sleep(0.5)
    a = browser.find_element_by_xpath("//*[@class='cv-dialog-modal']")
    browser.execute_script("arguments[0].removeAttribute(arguments[1])", a)
    sleep(0.2)
    try:
        browser.find_element_by_xpath("//*[@class='cv-sure cvBtnFlag']").click()
    except:
        sleep(0.2)
    result = proxy.har
    panduan(result)


## 其他选课
def other():
    search()
    sleep(0.5)
    browser.find_element_by_xpath("//*[@coursenumber='{}']".format(courseForSearch)).click()
    browser.find_element_by_xpath("//*[contains(@id,'{}')]".format(courseForSearch)).click()  # 展开详情
    sleep(0.2)
    try:
        browser.find_element_by_xpath(
            "//*[@class='cv-btn cv-btn-chose'and contains(@tcid,'{}')]".format(course)).click()  # 选择按钮
    except:
        print("人数已满")
    result = proxy.har  # 获取监听结果
    panduan(result)


def select():
    global n, tip
    if "成功" not in tip:
        sleep(1)
        print(strftime('%H:%M:%S', localtime()), "第%d次尝试" % n)
        n = n + 1
        if classid == "":
            publish()
        else:
            other()
    if "成功" in tip:
        print("恭喜，选课成功！")
        print("点个★呗:https://github.com/nobodyXX/nobadyXX")
        print("结束程序,请关闭浏览器")
        sched.pause_job('interval_task')  # 暂停任务
select()


sched = BlockingScheduler(timezone='Asia/Shanghai')

sched.add_job(select, 'interval', max_instances=10, minutes=9, seconds=24, id='interval_task')


try:
    sched.start()
except (KeyboardInterrupt, SystemExit):  # 总是执行不到下一行，不知道为啥
    print("11212132")
    sched.shutdown()
except:
    sched.shutdown()

