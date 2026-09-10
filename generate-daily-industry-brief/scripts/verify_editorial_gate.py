#!/usr/bin/env python3
"""Verify that formal cards retain the required leadership-brief fields."""
from __future__ import print_function
import argparse, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

FIELDS = ("发生了什么", "为何值得关注", "行动/风险点", "研判")

class CardParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.cards=[]; self.current=None; self.tag=None; self.text=[]
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if tag=="article" and "story" in data.get("class","").split():
            self.current={"attrs":data,"fields":{}}; self.cards.append(self.current)
        if self.current and tag in ("dt","dd","p"):
            self.tag=tag; self.text=[]
    def handle_data(self,data):
        if self.tag: self.text.append(data)
    def handle_endtag(self,tag):
        if self.current and tag==self.tag:
            value="".join(self.text).strip()
            if tag=="dt": self.current["_label"]=value
            elif tag=="dd" and self.current.get("_label"):
                self.current["fields"][self.current.pop("_label")]=value
            self.tag=None; self.text=[]
        if tag=="article" and self.current:
            self.current=None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("html_file",type=Path)
    a=p.parse_args()
    text=a.html_file.read_text(encoding="utf-8")
    parser=CardParser(); parser.feed(text)
    issues=[]
    for index,card in enumerate(parser.cards):
        kind=card["attrs"].get("data-entry-kind","")
        if kind not in ("primary","date-observation","expanded","business-observation"): continue
        fields=card["fields"]
        for label in FIELDS:
            value=fields.get(label,"")
            if not value: issues.append("story %s lacks field: %s"%(index,label))
            elif len(value)<45: issues.append("story %s field is too short: %s"%(index,label))
        fact=fields.get("发生了什么","")
        if fact and not any(token in fact for token in ("年","月","日","项目","公告","采购","公司","亿元","万","发布","签约","开工","完成")):
            issues.append("story %s lacks a concrete fact cue"%index)
    print(json.dumps({"ok":not issues,"formal_card_count":len(parser.cards),"issues":issues},ensure_ascii=False,indent=2))
    return 0 if not issues else 2
if __name__=="__main__": sys.exit(main())
