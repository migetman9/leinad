from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.utils import download_file, create_tmp_file, database, till_white, till_end
import re

db = database()

def vote_dict(title, options, starter, once):
    if isinstance(options, str):
        options = options.split(",")
    thing = {"active":"1", "title":title, "admin":starter, "options":"", "users":"", "once":str(once)}
    for opt in options:
        thing[str(opt)] = "0"
        thing[str(opt) + "-users"] = ""
        thing["options"] = thing["options"] + ",%s" % (opt)
    thing["options"] = str(thing["options"]).strip(',')
    return thing

delete_all_votes = '\\bdelete all votes\\b'
@listen_to(delete_all_votes, re.IGNORECASE)
@respond_to(delete_all_votes, re.IGNORECASE)
def delete_votes(message):
    if message.is_approved('admin'):
        db.votes.delete_many({})
        message.send("All Votes Deleted")

vote_string = "\\bstart vote\\b %s %s %s" % (till_white, till_white, till_end)
@listen_to(vote_string, re.IGNORECASE)
@respond_to(vote_string, re.IGNORECASE)
def start_vote(message, once, title, options):
    if message.is_approved('any'):
        vote_start = "Vote \"%s\" started.\nPlease Vote with 'vote %s (option)'\n" % (title, title)
        optss = ""
        for opt in options.split(","):
            optss += opt + '\n'
        if db.votes.count({"title":str(title)}) == 0:
            yes_once = once == "once"
            db.votes.insert_one(vote_dict(title, options, message.body['user'], yes_once))
            message.send(vote_start)
            message.upload_snippet(optss, "Options")
    else:
        message.send("User does not have sufficient permission.")

vote_end = "\\bend vote\\b %s" % till_white
@listen_to(vote_end, re.IGNORECASE)
@respond_to(vote_end, re.IGNORECASE)
def end_vote(message, title):
    if message.is_approved('any'):
        if db.votes.count({"title":title}) != 0:
            thing = db.votes.find({"title":title})
            for x in thing:
                if int(x['active']) == 1:
                    if message.body['user'] == x['admin']:
                        db.votes.update_one({"title":title}, {"$set": {"active": "0"}})
                        message.send("Vote Ended.\nResults:")
                        list_votes(message, title)
                else:
                    message.send("Vote not active.")


vote_option = "\\badd vote\\b %s %s" % (till_white, till_end)
@listen_to(vote_option, re.IGNORECASE)
@respond_to(vote_option, re.IGNORECASE)
def add_vote_option(message, title, option):
    if message.is_approved('any'):
        if db.votes.count({"title":title}) != 0:
            thing = db.votes.find({"title":title})
            for x in thing:
                if int(x['active']) == 1:
                    if message.body['user'] == x['admin']:
                        db.votes.update_one({"title":title}, {"$set": {"options": x['options'] + ",%s" % (option),
                                                                       option:"0",
                                                                       "%s-users" % (option):""}})
                        message.send("Option %s added" % option)
                    else:
                        message.send("Vote no longer active")



vote_add = "\\bvote\\b %s %s" % (till_white, till_end)
@listen_to(vote_add, re.IGNORECASE)
@respond_to(vote_add, re.IGNORECASE)
def add_vote(message, title, vote):
    if message.is_approved("any"):
        for x in message._client.users.keys():
            if message._client.users[x]['id'] == message.body['user']:
                votes = db.votes.find({"title":title})
                for v in votes:
                    if int(v['active']) == 1:
                        if title in v['title']:
                            try:
                                test = v[vote]
                                if message.body['user'] not in v[str(vote) + "-users"]:
                                    if message.body['user'] in v['users']:
                                        if v['once'] == str(True):
                                            message.send("User may only vote for one option.")
                                            return
                                    if vote in v["options"].split(","):
                                        db.votes.update_one({"title":title}, {"$set":{str(vote): str(int(v[vote]) + 1),
                                                                      "%s-users" % str(vote): (str(v["%s-users" % (vote)]) + ",%s" % (message.body['user'])).strip(','),
                                                                    "users": (str(v["users"]).replace("%s" % message.body['user'], "") + ",%s" % (message.body['user'])).strip(",")}})
                                        list_votes(message, title)
                                else:
                                    message.send("User has already voted.")
                            except IndexError:
                                message.send("Vote option %s does not exist" % vote)
                    else:
                        message.send("Vote not active.")

vote_list = "\\blist votes\\b %s" % (till_white)
vote_list2 = "\\blist vote\\b %s" % (till_white)

@listen_to(vote_list2, re.IGNORECASE)
@respond_to(vote_list2, re.IGNORECASE)
@listen_to(vote_list, re.IGNORECASE)
@respond_to(vote_list, re.IGNORECASE)
def list_votes(message, title):
    temp = ""
    if db.votes.count({"title": title}) != 0:
        thing = db.votes.find({"title": title})
        for x in thing:
            for y in str(x['options']).split(","):
                temp += "%s - %s\n" % (y, x[y])
        message.upload_snippet(temp, "Vote: %s options" % title)
    else:
        message.send("Vote does not exist")

vote_list = "\\blist votes-info\\b %s" % (till_white)
@listen_to(vote_list, re.IGNORECASE)
@respond_to(vote_list, re.IGNORECASE)
def list_votes_info(message, title):
    temp = ""
    if db.votes.count({"title": title}) != 0:
        thing = db.votes.find({"title": title})
        for x in thing:
            for y in str(x['options']).split(","):
                temp += "%s - %s\n" % (y, x[y])
                for z in x[y+ "-users"].split(','):
                    temp += "\t%s" % z
                temp += "\n"


        message.upload_snippet(temp, "Vote: %s options" % title)
    else:
        message.send("Vote does not exist")

