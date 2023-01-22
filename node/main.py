import numpy as np
import hashlib
import os
import json
import sys
import time
import base58
import ecdsa
import random
import string

#block function
coins = {}
blocks = []

def checkNewBlock(block):
    #check if block is the newest it can be
    if not block['id'] == len(blocks):
        return False

    #check if time is not in the future
    if time.time() < block['timeHashed']:
        return False

    #check if preHash is correct
    if not len(blocks) == 0:
        if not hashlib.sha256(json.dumps(blocks[len(blocks)-1]).encode('utf-8')).hexdigest() == block['preHashed']:
            print(blocks[len(blocks)-1])
            print(hashlib.sha256(json.dumps(blocks[len(blocks)-1]).encode('utf-8')).hexdigest())
            return False

    #check for preHash, reward Wallet and hashBiass Size
    if not len(blocks) == 0:
        if not len(block['preHashed']) == 64:
            return False

        if len(block['reward']['wallet']) > 126:
            return False

        if not block['reward']['coins'] == 10:
            return False
    
    #check for right difficulty
    blockTimes = []

    for i in blocks:
        if i['id'] > block['id'] - 8:
            blockTimes.append(i['timeHashed'])
    
    listTime = []

    for i in range(len(blockTimes)):
        if (i + 1) % 2 == 0:
            listTime.append(blockTimes[i] - blockTimes[i-1])
    
    if len(listTime) == 0:
        difficulty = 16
    else:
        avrTime = np.sum(listTime)
        difficulty = blocks[len(blocks)-1]['difficulty']
        if avrTime > 300:
            difficulty -= 1
        else:
            difficulty += 1

    if not len(blocks) == 0:
        timeDuration = round((block['timeHashed'] - blocks[len(blocks)-1]['timeHashed']) / 60)
        for _ in range(timeDuration):
            if difficulty > 0:
                difficulty -= 1

    if not block['difficulty'] == difficulty:
        return False

    #check if difficulty is reached
    copyBlock = json.loads(json.dumps(block))
    del copyBlock['noiseSeed']
    del copyBlock['hashBiass']

    random.seed(block['noiseSeed'])
    challenge = {
        'blockHash': hashlib.sha256(str(json.dumps(copyBlock)).encode('utf-8')).hexdigest(),
        'noise': ''.join(random.choices(string.hexdigits, k=64)),
        'hashBiass': block['hashBiass'],
    }

    hashedBlock = hashlib.sha256(str(json.dumps(challenge)).encode('utf-8')).digest()

    scoreString = ''
    for part in hashedBlock:
        bin = '{0:b}'.format(part)
        for _ in range(8 - len(bin)):
            bin += '0'

        scoreString += bin[::-1]

    score = len(scoreString.split('1')[0])
    if not score >= block['difficulty']:
        return False

    #validate all transactions
    for transaction in block['transactions']:
        #check type
        if not (transaction['type'] == 0 or transaction['type'] == 1):
            return False

        #check wallet sizes
        if len(transaction['from']) > 126 or len(transaction['to']) > 126:
            return False
        
        #check time
        if transaction['time'] > time.time():
            return False

        #check signature
        voucher = bytes(transaction['from'] + ', ' + str(transaction['amount']) + ', ' + str(transaction['fee']) + ' => ' + transaction['to'], 'utf-8')
        
        publicKeyFrom = ecdsa.VerifyingKey.from_string(base58.b58decode(transaction['from'].encode('utf-8')), curve=ecdsa.SECP256k1)
        signature = base58.b58decode(transaction['signature'].encode('utf-8'))
        
        try:
            publicKeyFrom.verify(signature, voucher)
        except ecdsa.keys.BadSignatureError:
            return False

        #check for funds
        if not coins[transaction['from']] >= transaction['amount'] + transaction['fee']:
            return False
    
    return True

#fund functions
def addFunds(wallet, amount):
    try:
        coins[wallet] += amount
    except:
        coins[wallet] = amount

def removeFunds(wallet, amount):
    coins[wallet] -= amount

#loading files
def firstNumber(a):
    return int(a.split('.json')[0])

blockFiles = os.listdir('./blocks/')
blockFiles.sort(key=firstNumber)

#load all saved blocks
for fileBlock in blockFiles:
    block = json.loads(open('./blocks/' + fileBlock, 'r').read())
    success = checkNewBlock(block)

    if not success:
        print('Failed to load saved block to chain!')
        sys.exit()
    else:
        #add block to chain and sent the funds in all transactions
        blocks.append(block)

        totalFees = 0
        for transaction in block['transactions']:
            addFunds(transaction['to'], transaction['amount'])
            removeFunds(transaction['from'], transaction['amount'] + transaction['fee'])

            totalFees += transaction['fee'] / 2

        addFunds(block['reward']['wallet'], block['reward']['coins'] + totalFees)
