from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.settings import db
from slackbot.utils import download_file, create_tmp_file, till_white, till_end
from slackbot.settings import botname
import re

"""
The Goal is to make an individual to-do list for every person.
"""

def to_do_dict(owner):
    return {"owner":owner, "items":""}

t_list = "\\bto-do list\\b"
@listen_to(t_list, re.IGNORECASE)
@respond_to(t_list, re.IGNORECASE)
def list_to_do_items(message):
    if message.is_approved("any"):
        o_d = {"owner":message.sent_by()}
        if db.todo.count(o_d) == 0:
            message.send("You don't have a to-do list.\nAdd one with 'to-do add (text)'")
        else:
            temp = ""
            count = 1
            for x in db.todo.find(o_d):
                for y in x['items'].split(","):
                    temp += "%d. %s\n" % (count, y)
                    count += 1
                message.upload_snippet(temp, "To-Do List of %s" % message.sent_by())

t_add = "\\bto-do add\\b %s" % till_end
t_add_help = "to-do add (text) - Separate items with commas"
@listen_to(t_add, re.IGNORECASE, t_add_help)
@respond_to(t_add, re.IGNORECASE, t_add_help)
def add_to_do_items(message, items):
    temp = items.split(",")
    items = ""
    for x in temp:
        items += x.strip(" ") + ","
    items.strip(",")
    if message.is_approved("any"):
        o_d = {"owner":message.sent_by()}
        if db.todo.count(o_d) == 0:
            db.todo.insert_one(to_do_dict(message.sent_by()))
        for x in db.todo.find(o_d):
            db.todo.update_one(o_d, {"$set":{"items": str(x['items'] + "," + items).strip(",")}})
            message.send("To-do list updated.")

t_remove = "\\bto-do remove\\b %s" % till_white
t_remove_help = "to-do remove (#) - Removes the task with the associated digit"
@listen_to(t_remove, re.IGNORECASE, t_remove_help)
@respond_to(t_remove, re.IGNORECASE, t_remove_help)
def remove_to_do_item(message, item):
    if message.is_approved("any"):
        o_d = {"owner":message.sent_by()}
        if db.todo.count(o_d) == 0:
            message.send("You don't have a to-do list.\nAdd one with 'to-do add (text)'")
        else:
            for x in db.todo.find(o_d):
                try:
                    test = x['items'].split(',')
                    rem = test[int(item)-1]
                    at_rem = x['items'].partition(rem)
                    new_items = "%s%s" % (at_rem[0],(at_rem[2]))
                    new_items = new_items.replace(",,", ",").strip(",")
                    if new_items != "":
                        db.todo.update_one(o_d, {"$set":{
                            "items": new_items
                        }})
                    else:
                        db.todo.delete_many(o_d)
                    message.send("Task '%s' removed" % rem)
                except:
                    message.send("That wasn't a number")

t_done = "\\bto-do finish\\b %s" % till_white
t_done_help = "to-do finish (#) - Marks the task with the associated digit with DONE"
@listen_to(t_done, re.IGNORECASE, t_done_help)
@respond_to(t_done, re.IGNORECASE, t_done_help)
def finish_to_do_item(message, item):
    if message.is_approved("any"):
        o_d = {"owner":message.sent_by()}
        if db.todo.count(o_d) == 0:
            message.send("You don't have a to-do list.\nAdd one with 'to-do add (text)'")
        else:
            for x in db.todo.find(o_d):
                try:
                    rem = x['items'].split(',')[int(item)-1]
                    at_rem = x['items'].partition(rem)
                    new_items = "%sDONE-%s" % (at_rem[0],(at_rem[1] + at_rem[2]))
                    if "DONE-" not in rem[0-5]:
                        db.todo.update_one(o_d, {"$set":{
                            "items": new_items
                        }})
                    message.send("Task '%s' marked as complete" % rem)
                except IndexError:
                    message.send("That task wasn't found")