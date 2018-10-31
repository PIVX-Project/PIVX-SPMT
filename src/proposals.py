#!/usr/bin/env python3
# -*- coding: utf-8 -*-

vote_index = {
    "YES": 1,
    "ABSTAIN": 0,
    "NO": -1
    }

vote_type = {
    "1": "YES",
    "0": "ABSTAIN",
    "-1": "NO"
    }

class Proposal():
    def __init__(self, name, URL, Hash, FeeHash, BlockStart, BlockEnd, TotalPayCount, RemainingPayCount, 
                 PayMentAddress, Yeas, Nays, Abstains, TotalPayment, MonthlyPayment):
        self.name = name
        self.URL = URL if URL.startswith('http') or URL.startswith('https') else 'http://'+URL
        self.Hash = Hash
        self.FeeHash = FeeHash
        self.BlockStart = int(BlockStart)
        self.BlockEnd = int(BlockEnd)
        self.TotalPayCount = int(TotalPayCount)
        self.RemainingPayCount = int(RemainingPayCount)
        self.PaymentAddress = PayMentAddress        
        self.Yeas = int(Yeas)
        self.Nays = int(Nays)
        self.Abstains = int(Abstains)
        self.ToalPayment = TotalPayment
        self.MonthlyPayment = MonthlyPayment
        ## list of personal masternodes voting
        self.MyYeas = []
        self.MyAbstains = []
        self.MyNays = []


#class ProjectedProposal():
#    def __init__(self, name, Hash, Allotted, Votes, TotalAllotted):
#        self.name = name
#        self.Hash = Hash
#        self.Allotted = Allotted
#        self.Votes = Votes
#        self.TotalAllotted = TotalAllotted