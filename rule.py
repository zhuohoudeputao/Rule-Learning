# Rule Learning

# import
from data import FEATURE, WATERMELON, LABEL
import copy
# 15.1


class Literal:
    # The class of literal
    # one literal means a test expression for attrs
    def __init__(self):
        pass


class AtomicFormula(Literal):
    # The class of atomic formula
    # one atomic formula means a relation
    f = None
    argNum = 0
    measure = ["forall"]  # or "exists"

    def __init__(self, f=None, argNum=0):
        super().__init__()
        self.f = f
        self.argNum = argNum

    def judge(self, *value):
        return f(*value)


class AtomicProp(Literal):
    # one atomic proposition means attr = value
    # 这里也是简化的表示，对于西瓜数据集来说
    # 原子命题的表示就只有“属性=属性值”，例如“根蒂=蜷缩”
    attr = ""
    value = ""

    def __init__(self, attr="", value=""):
        super().__init__()
        self.attr = attr
        self.value = value

    def __str__(self):
        return "%s=%s" % (self.attr, self.value)

    def __eq__(self, other):
        return self.attr == other.attr and self.value == other.value

    def judge(self, value, attr):
        if self.attr == attr and self.value == value:
            return True
        else:
            return False


class Head:
    # The class of head
    # one head means the result of a rule
    # 实际上Head的作用就是指示了规则所要判断的结果
    # 对于西瓜数据集来说，就是“好瓜”或“不是好瓜”，只有两种状态
    # 但对多分类问题来说，这个state就不能只是True和False了
    head = ""
    state = True

    def __init__(self, head="", state=True):
        self.head = head
        self.state = state

    def __str__(self):
        if self.state:
            return self.head
        else:
            return "not%s" % (self.head)

    def setState(self, state):
        self.state = state

    def switchState(self):
        self.state = not self.state


class Rule:
    # The class of rule
    # one rule contains
    # 1. the result, which is an object of Head
    # 2. a literal sequence with "and" relation between them
    # 这里为了简单，规则中文字之间只有合取
    def __init__(self, head, literalSequence=[]):
        self.head = head
        self.rule = literalSequence

    def addLiteral(self, literal):
        self.rule.append(literal)

    def extendLiteral(self, literalSequence):
        self.rule.extend(literalSequence)

    # 这里的pos还是从0算起，所以假设要替换第2个，应该传入1
    def replaceLiteral(self, literal, pos):
        self.rule[pos] = literal

    def __str__(self):
        string = ""
        string = string + self.head.__str__() + " <-- "
        length = len(self.rule)
        i = 0
        while i < length - 1:
            string = string + self.rule[i].__str__() + " and "
            i += 1
        if i < length:
            string = string + self.rule[i].__str__()
        return string

    def __len__(self):
        return len(self.rule)

    def __getitem__(self, item):
        return self.rule[item]


class RuleSet:

    def __init__(self, rules=[]):
        self.rules = rules

    def appendRule(self, rule):
        self.rules.append(rule)

    def extendRule(self, rules):
        self.rules.extend(rules)

    def __len__(self):
        return len(self.rules)

    def __getitem__(self, item):
        return self.rules[item]

    def print(self):
        for i in range(len(self.rules)):
            print(self.rules[i])

# 15.2


class Data:
    # 管理数据的一个类，为数据提供了一些便利的访问
    def __init__(self, feature, data, label):
        self.feature = feature
        self.data = data
        self.label = label

    def getSampleNum(self):
        return len(self.data)

    def getFeatureNum(self):
        return len(self.feature)

    def getFeatureIndex(self, feature):
        return self.feature.index(feature)

    def getLiteral(self, dataIndex, featureIndex):
        return AtomicProp(self.feature[featureIndex], self.data[dataIndex][featureIndex])

    # 一开始这里面没有加self导致出错的结果，原来是因为全局变量的原因
    def getLabel(self, dataIndex):
        if isinstance(dataIndex, list):
            return [self.label[index] == '是' for index in dataIndex]
        else:
            return self.label[dataIndex] == '是'

    def getPositiveSampleNum(self):
        ps = 0
        for i in range(len(self.label)):
            if self.label[i] == '是':
                ps += 1
        return ps

    # 不重复地生成文字
    def getFeatureDict(self, skip=[]):
        dataIndex = 0
        featureIndex = 0
        sampleNum = self.getSampleNum()
        atomicPropContainer = [[] for i in range(len(self.feature))]
        for dataIndex in range(self.getSampleNum()):
            if dataIndex in skip:
                continue
            for featureIndex in range(self.getFeatureNum()):
                literalNow = self.getLiteral(dataIndex, featureIndex)
                if literalNow not in atomicPropContainer[featureIndex]:
                    atomicPropContainer[featureIndex].append(literalNow)
        return atomicPropContainer

    # 返回规则包不包括该特征的一个状态，例如[False, True, False,...]
    def getCoveredFeature(self, rule):
        coveredFeature = [False] * self.getFeatureNum()
        ruleAttr = []
        for i in range(len(rule)):
            ruleAttr.append(rule[i].attr)
        for i in range(self.getFeatureNum()):
            if self.feature[i] in ruleAttr:
                coveredFeature[i] = True
        return coveredFeature

    # skip可以用来传入已经去除掉的样例序号，相当于在数据集中去掉该样例
    def getCoveredSample(self, rule, skip=[]):
        # get the indexes of data covered by rule
        indexSet = []
        # 对每个样例都排查一遍
        for i in range(len(self.data)):
            if i in skip:
                continue
            covered = True
            # 逐个检查样例中的“属性、属性值”是不是被规则中的“属性=属性值”覆盖
            for j in range(len(rule)):
                literal = rule[j]
                covered = self.getLiteralCover(rule[j], i)
                if covered == False:
                    break
            if covered == True:
                indexSet.append(i)
        return indexSet

    def getLiteralCover(self, literal, dataIndex):
        # judge if the attr of sample is covered by literal or not
        # 本来是没有文字覆盖样例这种说法的
        # 但是实际上在判断就是每个文字对一个样例进行判断
        # 首先查看这个文字的属性有没有在数据里
        featureIndex = 0
        while featureIndex < self.getFeatureNum():
            if self.feature[featureIndex] == literal.attr:
                break
            featureIndex += 1
        if featureIndex == self.getFeatureNum():
            return False
        # 然后判断这个样例的属性值是否跟文字的属性值一样
        else:
            return self.data[dataIndex][featureIndex] == literal.value

    # 测试函数，这里暂时用到准确率，以后有需要还可以继续加
    def test(self, rule, skip=[]):
        covered = self.getCoveredSample(rule, skip)
        TP, FP, FN, TN = 0, 0, 0, 0
        for i in covered:
            if self.getLabel(i) == True:
                TP += 1
            else:
                FP += 1
        if TP + FP == 0:
            precision = 0
        else:
            precision = TP / (TP + FP)
        # recall = TP/data.getPositiveSampleNum()
        return TP+FP, precision


def SerialCover():
    # 一开始用整个数据集怎么都做不出结果
    # 最后发现是用P80页上半部分（训练集）做的
    trainData = [0, 1, 2, 5, 6, 9, 13, 14, 15, 16]
    train_watermelon, train_label = [], []
    for i in trainData:
        train_watermelon.append(WATERMELON[i])
        train_label.append(LABEL[i])
    data = Data(FEATURE, train_watermelon, train_label)
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
                rule = Rule(Head("好瓜"), [])  # 创建一个新的规则
                for i in range(len(index)):
                    rule.addLiteral(featureDict[combine[i]][index[i]])
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
                    if len(coverSet) == data.getPositiveSampleNum():
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


def BeamSearch(b):
    # b是每轮保留的数量，当然不能太大
    coverSet = []
    R = RuleSet([])
    rules = [Rule(Head("好瓜"))]
    # 数据还是西瓜数据集2.0的训练集
    trainData = [0, 1, 2, 5, 6, 9, 13, 14, 15, 16]
    train_watermelon, train_label = [], []
    for i in trainData:
        train_watermelon.append(WATERMELON[i])
        train_label.append(LABEL[i])
    data = Data(FEATURE, train_watermelon, train_label)
    TopDown(data, R, coverSet, b, rules)
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
            ruletmp.addLiteral(featureList[i])
            # print(ruletmp)
            # 测试
            coverNum, precision = data.test(ruletmp, coverSet)
            gradeTable.append((ruletmp, precision, coverNum, data.getFeatureNum(
            )-data.getFeatureIndex(featureList[i].attr)))
    # 输出gradeTable看看
    # for i in gradeTable:
    #     print(*i)
    # 对gradeTable进行排序, 优先是precision，然后是coverNum，最后是属性次序靠前
    from operator import itemgetter
    gradeTable = sorted(gradeTable, key=itemgetter(1, 2, 3), reverse=True)
    # 输出gradeTable看看
    # for i in gradeTable:
    #     print(*i)
    # 如果出现了覆盖率为100%的规则，那么将该规则加入到R当中, 把当前规则覆盖的样例序号加入到coverSet中
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
    # 递归结束后看看是否已经完成了，还没完成的话还要从头开始
    if len(coverSet) != data.getPositiveSampleNum():
        TopDown(data, R, coverSet, b, [Rule(Head("好瓜"))])


if __name__ == "__main__":
    SerialCover().print()
    print()
    BeamSearch(1).print()
    print()
    BeamSearch(2).print()
