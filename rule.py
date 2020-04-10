# Rule Learning

# import
from data import FEATURE, WATERMELON, LABEL

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
    # The class of atomic proposition
    # one atomic proposition means attr = value
    attr = ""
    value = ""

    def __init__(self, attr="", value=""):
        super().__init__()
        self.attr = attr
        self.value = value

    def __str__(self):
        return "%s = %s" % (self.attr, self.value)

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
        if self.label[dataIndex] == '是':
            return True
        else:
            return False

    def getPositiveSampleNum(self):
        ps = 0
        for i in range(len(self.label)):
            if self.label[i] == '是':
                ps += 1
        return ps

    def getRuleCover(self, rule, skip=[]):
        # get the indexes of data covered by rule
        indexSet = []
        for i in range(len(self.data)):
            if i in skip:
                continue
            covered = True
            for j in range(0, len(rule)):
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

    # 这个是为了给序贯覆盖写的迭代器，用于对每个特征都生成所有的属性
    # 不重复地生成文字
    # 按照先增加样例的序号，再增加特征的序号进行
    def __iter__(self):
        self.iter_dataIndex = 0
        self.iter_featureIndex = 0
        self.literalContainer = []
        return self

    def __next__(self):
        while self.iter_dataIndex < self.getSampleNum() and self.iter_featureIndex < self.getFeatureNum():
            literalNow = self.getLiteral(
                self.iter_dataIndex, self.iter_featureIndex)
            literalFeatureIndex = self.iter_featureIndex
            self.iter_dataIndex += 1
            if self.iter_dataIndex == self.getSampleNum():
                self.iter_dataIndex = 0
                self.iter_featureIndex += 1
            if literalNow not in self.literalContainer:
                self.literalContainer.append(literalNow)
                return literalNow, literalFeatureIndex
        raise StopIteration


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
    featureDict, currentFeatureIndex = [[]], 0  # 已二维的形式记录目前所有生成的文字
    dataIter = iter(data)  # 生成不重复的文字的迭代器
    # 觉得与其每到用完的时候再生成，不如直接全部生成更划算一点
    for literalNow, featureIndex in dataIter:
        if currentFeatureIndex != featureIndex:
            featureDict.append([])
            currentFeatureIndex += 1
        featureDict[currentFeatureIndex].append(literalNow)

    # 然后是进行序贯覆盖
    R = []  # 规则集
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
                coverSet_tmp = data.getRuleCover(rule, coverSet)
                result = list(
                    map(lambda dataIndex: data.getLabel(dataIndex), coverSet_tmp))
                allPositive = result.count(True) == len(result)
                # for dataIndex in coverSet_tmp:
                #     allPositive = allPositive and data.getLabel(dataIndex)
                # 对规则集进行更新
                if allPositive == True and coverSet_tmp != []:
                    R.append(rule)
                    print(rule)
                    coverSet.extend(coverSet_tmp)
                    print("coverSet", coverSet)
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
                    combine[pos-1:] = a


def TopDown():

    pass


SerialCover()
