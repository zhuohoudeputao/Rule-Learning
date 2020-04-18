import math
# 15.1
# 把所有基本概念都写成了类


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
    # 对于西瓜数据集来说，head就是“好瓜”，是我们要去判断的东西
    # 而state就是指“是”或“否”，是我们判断的结果
    def __init__(self, head, state):
        self.head = head
        self.state = state

    def __str__(self):
        return "%s:%s" % (self.head, self.state)

    def setState(self, state):
        self.state = state

    # def switchState(self):
    #     self.state = not self.state

class Complex:
    def __init__(self, literalSequence=[]):
        self.cpx = literalSequence

    def appendLiteral(self, literal):
        self.cpx.append(literal)
    
    def extendLiteral(self, literalSequence):
        self.cpx.extend(literalSequence)
    
    def replaceLiteral(self, literal, pos):
        self.cpx[pos] = literal
    
    def __len__(self):
        return len(self.cpx)
    
    def __str__(self):
        string = ""
        length = len(self.cpx)
        i = 0
        while i < length - 1:
            string = string + self.cpx[i].__str__() + " and "
            i += 1
        if i < length:
            string = string + self.cpx[i].__str__()
        return string
    
    def __getitem__(self, item):
        return self.cpx[item]
    

class Rule:
    # 这里为了简单，规则中的文字之间只有合取
    # 一个规则由左右两边组成，左边是结果head，右边是文字的合取式complex
    def __init__(self, head, cpx=Complex()):
        self.head = head
        self.cpx = cpx

    def appendLiteral(self, literal):
        self.cpx.appendLiteral(literal)

    def extendLiteral(self, literalSequence):
        self.cpx.extendLiteral(literalSequence)

    # 这里的pos还是从0算起，所以假设要替换第2个，应该传入1
    def replaceLiteral(self, literal, pos):
        self.cpx[pos] = literal

    def __str__(self):
        return self.head.__str__() + " <-- " + self.cpx.__str__()
        
    def __len__(self):
        return len(self.cpx)

    def __getitem__(self, item):
        return self.cpx[item]


class RuleSet:
    # self.default = "是"
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


class Data:
    # 管理数据的一个类，为数据提供了一些便利的访问
    def __init__(self, feature, data, label):
        self.feature = feature
        self.data = data
        self.label = label
        # self.skip = {} # 用跳过代替删除

    # 获取样例数量，可以传入label获取指定label的样例数量，也可以传入skip删除部分样例
    def getSampleNum(self, label=None, skip=[]):
        if label == None:
            return len(self.data) - len(skip)
        else:
            sum = 0
            for i in range(len(self.label)):
                if i in skip:
                    continue
                elif self.label[i] == label:
                    sum += 1
            return sum

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

    # 不重复地生成文字表
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

    # 返回complex（规则右边的部分）包不包括该特征的一个状态，例如[False, True, False,...]
    def getCoveredFeature(self, cpx):
        coveredFeature = [False] * self.getFeatureNum()
        ruleAttr = []
        for i in range(len(cpx)):
            ruleAttr.append(cpx[i].attr)
        for i in range(self.getFeatureNum()):
            if self.feature[i] in ruleAttr:
                coveredFeature[i] = True
        return coveredFeature

    # skip可以用来传入已经去除掉的样例序号，相当于在数据集中去掉该样例
    # 实际上这里的rule也可以换做complex
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

    # 对规则的测试函数，这里暂时用到准确率，以后有需要还可以继续加
    def testRule(self, rule, skip=[]):
        # 先得到规则覆盖的那些样本
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
        return TP + FP, precision

    # 对complex进行测试的函数，返回complex的熵
    def testComplex(self, cpx, skip=[]):
        covered = self.getCoveredSample(cpx, skip)
        # 每一个label对应一个覆盖数
        coverDict = {}
        for dataindex in covered:
            if coverDict.get(self.label[dataindex]) == None:
                coverDict[self.label[dataindex]] = 0
            coverDict[self.label[dataindex]] += 1
        entropy, LRS = 0, 0
        for key in coverDict.keys():
            f = p = coverDict[key] / len(covered) # 每一个label出现的频率
            e = self.getSampleNum(label=key, skip=skip)/self.getSampleNum(skip=skip) # 数据集当中的分布
            entropy -= p*math.log2(p) # 为0的时候说明全部是同一类
            LRS += 2*f*math.log2(f/e) # 越大表明越不是猜的，规则和结果之间关联性比较大
        return entropy, LRS

    def getMostLabel(self, cpx, skip=[]):
        covered = self.getCoveredSample(cpx, skip)
        # 每一个label对应一个覆盖数
        coverDict = {}
        for dataindex in covered:
            if coverDict.get(self.label[dataindex]) == None:
                coverDict[self.label[dataindex]] = 0
            coverDict[self.label[dataindex]] += 1
        
        m = max(coverDict.values())
        for key in coverDict.keys():
            if coverDict[key] == m:
                return key

    # 对规则集的测试函数
    def testRuleSet(self, ruleSet):
        pass
