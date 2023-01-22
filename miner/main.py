import numpy as np
import keys
import hashlib
import json
import time
import random
import os
import string

key = keys.generate()
key.load()

#sorting key
def firstNumber(a):
    return int(a.split('.json')[0])

#loading blocks
blocks = []
blockFiles = os.listdir('./blocks/')
blockFiles.sort(key=firstNumber)

BlockID = 0
for fileBlock in blockFiles:
    blocks.append(json.loads(open('./blocks/' + fileBlock, 'r').read()))
    BlockID += 1


while True:
    #get pre hash map
    try:
        preHash = hashlib.sha256(json.dumps(blocks[len(blocks)-1]).encode('utf-8')).hexdigest()
    except:
        preHash = ''

    #get pre block time
    try:
        preTime = blocks[len(blocks)-1]['timeHashed']
    except:
        preTime = time.time()

    #get difficulty
    blockTimes = []

    for i in blocks:
        if i['id'] > len(blocks) - 8:
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

    #degrade difficulty over time
    timeDuration = round((time.time() - preTime) / 60)
    for _ in range(timeDuration):
        if difficulty > 0:
            difficulty -= 1

    newBlock = {
        "id": len(blocks),
        "preHashed": preHash,
        "transactions": [],
        "reward": {
            "coins": 10,
            "wallet": key.stringPublicKey
        },
        "difficulty": difficulty,
        "timeHashed": time.time()
    }

    noiseSeed = random.randint(0, 10**32)
    preSeed = random.seed()
    random.seed(noiseSeed)
    challenge = {
        'blockHash': hashlib.sha256(str(json.dumps(newBlock)).encode('utf-8')).hexdigest(),
        'noise': ''.join(random.choices(string.hexdigits, k=64)),
        'hashBiass': 0,
    }

    random.seed(preSeed)

    for _ in range(100000):
        challenge['hashBiass'] = random.randint(0, 10**32)
        hashedBlock = hashlib.sha256(str(json.dumps(challenge)).encode('utf-8')).digest()

        scoreString = ''
        for part in hashedBlock:
            bin = '{0:b}'.format(part)
            for _ in range(8 - len(bin)):
                bin += '0'

            scoreString += bin[::-1]

        score = len(scoreString.split('1')[0])

        if score > difficulty:
            newBlock['noiseSeed'] = noiseSeed
            newBlock['hashBiass'] = challenge['hashBiass']

            print('Found Block!', score, newBlock)
            blocks.append(newBlock)
            open('./blocks/' + str(BlockID) + '.json', 'w').write(json.dumps(newBlock, indent=4))
            BlockID += 1
            break
        if score > 15:
            print('Got close to', difficulty, 'reached', score)