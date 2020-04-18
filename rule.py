# import
from data import FEATURE, WATERMELON, LABEL
import copy
from classes import *
from operator import itemgetter
# 15.2


def SerialCover(data):
    # 首先第一步是生成文字表（突然想到可以直接写在Data类里）
    # 已二维的形式记录目前所有生成的文字
    featureDict = data.getFeatureDict()

    # 然后是进行序贯覆盖
    R = RuleSet()  # 规则集
    coverSet = []  # 记录已经被规则集覆盖的样本
    currentL = 0  # 当前规则的长度
    completed = False
    while currentL < data.getFeatureNum() and not completed:
        currentL += 1
        # combine 用来记录当前结合生成规则的特征位置
        combine = [0+i for i in range(currentL)]
        currentLCompleted = False
        while currentLCompleted == False and not completed:
            # print("combine", combine)
            currentCombineCompleted = False
            # 就像一个二维表一样，为了得到所需长度currentL的规则
            # 不仅需要知道我们在哪些Feature里面取值，也就是combine
            # 还需要知道我们取的是Feature的第几个值，这就是👈index
            index = [0]*len(combine)
            while currentCombineCompleted == False and not completed:
                # 生成规则
                rule = Rule(Head("好瓜", "是"), Complex([]))  # 创建一个新的规则
                for i in range(len(index)):
                    rule.appendLiteral(featureDict[combine[i]][index[i]])
                # print(rule)
                # 测试规则
                allPositive = True
                # 这样子实现对于二分类问题，当我们需要判断反例的时候只需要把True改为False
                coverSet_tmp = data.getCoveredSample(rule, coverSet)
                result = list(
                    map(lambda dataIndex: data.getLabel(dataIndex), coverSet_tmp))
                allPositive = result.count(True) == len(result)
                # for dataIndex in coverSet_tmp:
                #     allPositive = allPositive and data.getLabel(dataIndex)
                # 对规则集进行更新
                if allPositive == True and coverSet_tmp != []:
                    R.appendRule(rule)
                    print(rule)
                    coverSet.extend(coverSet_tmp)
                    print("coverSet", coverSet)
                    # 当coverSet当中的正例数已经达到数据集的正例数，就结束
                    if len(coverSet) == data.getSampleNum(label="是"):
                        completed = True
                        break
                else:
                    # 更新index，优先更换最后一个
                    index[-1] += 1
                    for i in range(len(index)-1, 0, -1):
                        if index[i] == len(featureDict[combine[i]]):
                            index[i] = 0
                            index[i-1] += 1
                    if index[0] == len(featureDict[combine[0]]):
                        currentCombineCompleted = True
            # 当前的combine遍历完之后更新combine
            # 首先尝试对combine的最后一个位置加1
            pos = len(combine) - 1
            if combine[pos] < len(featureDict) - 1:
                combine[pos] += 1
            else:
                # 先对L=1的情况进行特殊处理
                if pos == 0:
                    currentLCompleted = True
                    break
                # 不行再往前找到第一个能更新的位置 pos-1
                while combine[pos-1]+1 == combine[pos]:
                    pos -= 1
                    if pos == 0:
                        # 说明当前的combine已经不能再更新了，也就是当前的长度已经走完了
                        currentLCompleted = True
                        break
                if pos != 0:
                    # 这时对当前能更新的位置进行更新
                    a = [i for i in range(
                        combine[pos-1]+1, combine[pos-1]+1+len(combine)-pos+1)]
                    combine[pos - 1:] = a
    return R


def BeamSearch(data, b):
    # b是每轮保留的数量，当然不能太大
    coverSet = []
    R = RuleSet([])
    # rules = [Rule(Head("好瓜", "是"), Complex([]))]
    # # 数据还是西瓜数据集2.0的训练集
    # trainData = [0, 1, 2, 5, 6, 9, 13, 14, 15, 16]
    # train_watermelon, train_label = [], []
    # for i in trainData:
    #     train_watermelon.append(WATERMELON[i])
    #     train_label.append(LABEL[i])
    # data = Data(FEATURE, train_watermelon, train_label)
    # 递归结束后看看是否已经完成了，还没完成的话还要从头开始
    while len(coverSet) != data.getSampleNum(label="是"):
        TopDown(data, R, coverSet, b, [Rule(Head("好瓜", "是"), Complex([]))])
    return R


def TopDown(data, R, coverSet, b, rules):
    # 可以写成递归的形式，当coverSet覆盖了所有正例的时候终止
    # 每次传到下一层的时候是把当前留下来的b个规则传到下面去
    # 同样的，对于自顶向下的问题，因为是一轮一轮进行扫描，而每轮只添加一个新的
    # 首先是获取二维文字集，那么这个时候在每一层当中要考虑把已经覆盖的那些正例去除掉，再生成FD
    featureDict = data.getFeatureDict(coverSet)
    gradeTable = []  # 得分表，用来存放拓展出来的规则还有相应的得分、覆盖数、属性次序
    # 对于传进来的每个规则，都要进行文字的添加
    for rule in rules:
        # 我们要先看它覆盖了多少个特征，然后把这些特征的属性值去掉
        coveredFeature = data.getCoveredFeature(rule)
        featureList = []  # 同时把没有覆盖的特征对应的文字变成一个列表
        for i in range(len(featureDict)):
            if coveredFeature[i] == False:
                featureList.extend(featureDict[i])
        # print(*featureList)
        # print(rule)
        # 对featureList里面的每一个文字都加到规则中，然后记录结果
        for i in range(len(featureList)):
            # 这里要使用深拷贝，每次产生一个新规则
            ruletmp = copy.deepcopy(rule)
            ruletmp.appendLiteral(featureList[i])
            # print(ruletmp)
            # 测试
            coverNum, precision = data.testRule(ruletmp, coverSet)
            gradeTable.append((ruletmp, precision, coverNum, data.getFeatureNum(
            )-data.getFeatureIndex(featureList[i].attr)))
    # 输出gradeTable看看
    # for i in gradeTable:
    #     print(*i)
    # 对gradeTable进行排序, 优先是precision，然后是coverNum，最后是属性次序靠前
    gradeTable = sorted(gradeTable, key=itemgetter(1, 2, 3), reverse=True)
    # 输出gradeTable看看
    # for i in gradeTable:
    #     print(*i)
    # 如果出现了准确率为100%的规则，那么将该规则加入到R当中, 把当前规则覆盖的样例序号加入到coverSet中
    best = gradeTable[0]
    if best[1] == 1:
        R.appendRule(best[0])
        print(best[0])
        coverSet.extend(data.getCoveredSample(best[0], coverSet))
        print(coverSet)
        return  # 把一个规则添加到规则集中，那么前面这些东西就要重新算了
    # 对最前面的b个进行进一步的递归
    newrules = []
    for i in range(b):
        newrules.append(gradeTable[i][0])
    TopDown(data, R, coverSet, b, newrules)


def CN2(data, b, LRS_threshold=0.99):
    # 跟集束搜素一样需要一个参数b
    # 还需要另外的一个参数，就是LRS增长到什么时候停止生长
    coverSet = []
    R = RuleSet([])
    # 要注意CN2不是从“好瓜”这个头开始的，也就是说它的头可以是坏瓜
    # 对一个complex衡量的标准是熵的大小，熵越小，这个complex越好
    # cpxes = [Complex([])]
    CN2_TopDown(data, R, coverSet, b, [Complex([])], LRS_threshold)
    return R


def CN2_TopDown(data, R, coverSet, b, cpxes, LRS_threshold):
    featureDict = data.getFeatureDict(coverSet)
    gradeTable = []

    for cpx in cpxes:
        # 我们要先看它覆盖了多少个特征，然后把这些特征的属性值去掉
        coveredFeature = data.getCoveredFeature(cpx)
        featureList = []  # 同时把没有覆盖的特征对应的文字变成一个列表
        for i in range(len(featureDict)):
            if coveredFeature[i] == False:
                featureList.extend(featureDict[i])
        # 对featureList里面的每一个文字都加到规则中(特化)，然后记录结果
        for i in range(len(featureList)):
            # 这里要使用深拷贝，每次产生一个新complex
            cpxtmp = copy.deepcopy(cpx)
            cpxtmp.appendLiteral(featureList[i])
            # 测试(这里发生了不同，是去求熵和LRS)
            entropy, LRS = data.testComplex(cpxtmp, coverSet)
            # 因为熵是越小越好，LRS是越大越好
            gradeTable.append((cpxtmp, entropy, LRS))

    # 对gradeTable关于LRS进行排序（因为一旦有LRS>0.99, 就要生成一个规则）
    gradeTable = sorted(gradeTable, key=itemgetter(2), reverse=True)
    # 找到那些大于LRS阈值的complex
    maxlength = -1
    for i in range(len(gradeTable)):
        if gradeTable[i][2] >= LRS_threshold:
            maxlength += 1
    if maxlength != -1:
        # 如果出现了LRS大于阈值的complex，就找出熵最小的那个，然后生成一个规则
        satisfied = sorted(
            gradeTable[0: maxlength + 1], key=itemgetter(1))
        best = satisfied[0]
        # print(*best)
        head = Head("好瓜", data.getMostLabel(best[0], coverSet))
        rule = Rule(head, best[0])
        R.appendRule(rule)
        print(rule)
        coverSet.extend(data.getCoveredSample(rule, coverSet))
        print(coverSet)
        # 然后在这个基础上重新计算新的规则
        CN2_TopDown(data, R, coverSet, b, [Complex([])], LRS_threshold)
    else:
        # 否则对前面b个进行递归，此时需要取熵最小的b个
        # 但递归前还需要进行一些判断
        # complex已经是最长了，就是说再怎么加文字，它的LRS都没办法提高了，这时要考虑放大b或者降低LRS的阈值
        if len(gradeTable[0][0]) == data.getFeatureNum():
            return
        gradeTable = sorted(gradeTable, key=itemgetter(1))
        newcpxes = []
        for i in range(b):
            newcpxes.append(gradeTable[i][0])
        CN2_TopDown(data, R, coverSet, b, newcpxes, LRS_threshold)


if __name__ == "__main__":
    # 一开始用整个数据集怎么都做不出结果
    # 最后发现是用P80页上半部分（训练集）做的
    trainData = [0, 1, 2, 5, 6, 9, 13, 14, 15, 16]
    train_watermelon, train_label = [], []
    for i in trainData:
        train_watermelon.append(WATERMELON[i])
        train_label.append(LABEL[i])
    data = Data(FEATURE, train_watermelon, train_label)

    # SerialCover(data).print()
    # print()
    # BeamSearch(data, 1).print()
    # print()
    # BeamSearch(data, 2).print()
    # print()
    # 发现b参数的影响在这个数据下并不大，反而是LRS阈值的影响比较大
    # 也就是说如果已经找不到能达到LRS阈值的规则了，那么扩大
    CN2(data, 5).print()
    print()
    # 更改了LRS的阈值，发现最后训练集是有一个没有被覆盖的，可能这时需要加入一个默认规则
    CN2(data, 1, LRS_threshold=0.9).print()
