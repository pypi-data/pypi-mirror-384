# from diglife.core import get_score, score_from_memory_card, memory_card_polish



# def test_score_from_memory_card():
#     memory_card = """
#  {'title': '童年惊魂',
#   'content': '我记得在我小的时候，大概是在我三四年级的时候，我和我的小伙伴一块去上山抓蝎子。小时候那会儿都比较皮，到处跑。我在山上去翻蝎子的时候，遇到了一条蛇！我和它对视过后，我就慌忙地转身逃跑。在我刚转身逃跑的时候，我看见山上的小路上有一个树枝倒下来了，倒在我的前面，然后我就跳了起来。在我跳起来的时候，那条蛇就在我的脚底下钻过去了，当时真的吓得我很害怕。如果不是那个树枝的话，我可能就被咬了。而且那条蛇，我记得它是三角脑袋，枯草色的，看着像是有毒的样子。之后我对山上有些阴影了，都不怎么去上山抓蝎子了。我现在上山还是会拿根棍子，到处敲一敲！说实话，真的有阴影。'},
# """
#     result = score_from_memory_card(memory_card)
#     print(result)


# def test_memory_card_polish():
#     memory_card = """
#  {'title': '童年惊魂',
#   'content': '我记得在我小的时候，大概是在我三四年级的时候，我和我的小伙伴一块去上山抓蝎子。小时候那会儿都比较皮，到处跑。我在山上去翻蝎子的时候，遇到了一条蛇！我和它对视过后，我就慌忙地转身逃跑。在我刚转身逃跑的时候，我看见山上的小路上有一个树枝倒下来了，倒在我的前面，然后我就跳了起来。在我跳起来的时候，那条蛇就在我的脚底下钻过去了，当时真的吓得我很害怕。如果不是那个树枝的话，我可能就被咬了。而且那条蛇，我记得它是三角脑袋，枯草色的，看着像是有毒的样子。之后我对山上有些阴影了，都不怎么去上山抓蝎子了。我现在上山还是会拿根棍子，到处敲一敲！说实话，真的有阴影。'},
# """
#     result = memory_card_polish(memory_card)
#     print(result)

# from diglife.core import extract_person_name

# def test_extract_person_name():
#     bio_chunk = """

# """
#     result = extract_person_name(bio_chunk)
#     print(result)


# from diglife.core import extract_person_name, extract_person_place

# def test_extract_person_name():
#     bio_chunk = """
# ## 第五章 县城初中：混乱中的坚韧
# 小学时，我曾是班里的第一名，甚至在整个学校五六个年级中，我的成绩也名列前茅。那时的我，能够全身心地投入学习，没有太多杂念。然而，进入初中，环境却发生了翻天覆地的变化。我上的初中叫镇南初中，是我们县的第二初级中学。初二升初三时，学校与县里的第一初级中学合并，搬到了一个新建的校区。
# 新校区虽然是新建的，但环境远不如想象中那么完善，甚至可以说有些混乱。操场还是土的，没有铺设；一些下水管道和电线还没埋到地下，路上随处可见大沟。我清楚地记得，有一天晚上我们下晚自习，班里一个同学就因为路上太黑，加上有施工的坑，不小心掉了下去，胳膊当场就摔骨折了。这样的环境，无疑给原本就躁动的青春期增添了更多不安定的因素。
# 县城初中的生活，用“混乱”二字来形容，再贴切不过。几乎每周都会发生打架事件，而每两周，甚至会爆发一次群架。校园里弥漫着一股紧张而又野蛮的气息，许多同学在这种环境下逐渐迷失，最终选择了中途辍学。我亲眼看着身边的同学一个个离开，他们或是被卷入无休止的冲突，或是对学业彻底失去了兴趣。
# 面对这样的环境，我并没有选择随波逐流。虽然也曾参与过一些打架事件，甚至有一次头部被餐盘砸伤，但这并没有影响我对学业的坚持。我深知学习是我唯一的出路，也是我能掌控自己未来的关键。小学时养成的专注学习的习惯，在这里发挥了巨大的作用。即便周围充斥着喧嚣和冲突，我依然能够保持对知识的渴望，将大部分精力投入到学习中。我的成绩始终保持在班级名列前茅，甚至在全校也位居前十。这让许多同学家长都向他们的孩子提起我，甚至会向我请教学习方法。
# 在这混乱之中，我学会了如何生存，也学会了如何保护自己。我与几个要好的朋友组成了小团体。我们彼此扶持，共同面对校园里的各种挑战，形成了一种“团结对外”的默契。我的一个好友，就因为卷入打架事件，最终被父母领回沈阳。即便如此，我们之间的友谊也未曾中断，直到现在我们依然保持着联系，前段时间他还邀请我当他的伴郎。这段经历让我认识到，在逆境中，友谊和团结的力量是多么重要。
# 初中这段经历，对我性格的塑造产生了深远的影响。它让我过早地接触到了社会复杂的一面，也让我认识到自己身上“意气用事”的一面。在那个年纪，面对不公或挑衅，我常常会冲动行事。这种“意气用事”的特质，在后来的很长一段时间里都伴随着我。直到上大学，我才慢慢意识到这个问题，并逐渐开始修正。我不太清楚具体是怎么改的，就是逐渐地、慢慢地意识到了问题，然后慢慢地就改过来了。现在的我，在面对问题时，会更加理智地去判断。
# 回首那段岁月，我为自己能够坚持到毕业而感到庆幸。在许多同学中途辍学的大背景下，其中就包括我的朋友张望,
# 我的坚持，不仅是对学业的执着，更是对未来的一种信念。这段混乱而又充满挑战的初中生活，磨砺了我的意志，锻炼了我的环境适应能力，也奠定了我坚韧的性格底色。它让我明白，无论身处何种困境，只要心中有目标，并为之不懈努力，便能找到属于自己的出路。
# """
#     result = extract_person_name(bio_chunk)
#     print(result)

# def test_extract_person_place():
#     bio_chunk = """
# ## 第五章 县城初中：混乱中的坚韧
# 小学时，我曾是班里的第一名，甚至在整个学校五六个年级中，我的成绩也名列前茅。那时的我，能够全身心地投入学习，没有太多杂念。然而，进入初中，环境却发生了翻天覆地的变化。我上的初中叫镇南初中，是我们县的第二初级中学。初二升初三时，学校与县里的第一初级中学合并，搬到了一个新建的校区。
# 新校区虽然是新建的，但环境远不如想象中那么完善，甚至可以说有些混乱。操场还是土的，没有铺设；一些下水管道和电线还没埋到地下，路上随处可见大沟。我清楚地记得，有一天晚上我们下晚自习，班里一个同学就因为路上太黑，加上有施工的坑，不小心掉了下去，胳膊当场就摔骨折了。这样的环境，无疑给原本就躁动的青春期增添了更多不安定的因素。
# 县城初中的生活，用“混乱”二字来形容，再贴切不过。几乎每周都会发生打架事件，而每两周，甚至会爆发一次群架。校园里弥漫着一股紧张而又野蛮的气息，许多同学在这种环境下逐渐迷失，最终选择了中途辍学。我亲眼看着身边的同学一个个离开，他们或是被卷入无休止的冲突，或是对学业彻底失去了兴趣。
# 面对这样的环境，我并没有选择随波逐流。虽然也曾参与过一些打架事件，甚至有一次头部被餐盘砸伤，但这并没有影响我对学业的坚持。我深知学习是我唯一的出路，也是我能掌控自己未来的关键。小学时养成的专注学习的习惯，在这里发挥了巨大的作用。即便周围充斥着喧嚣和冲突，我依然能够保持对知识的渴望，将大部分精力投入到学习中。我的成绩始终保持在班级名列前茅，甚至在全校也位居前十。这让许多同学家长都向他们的孩子提起我，甚至会向我请教学习方法。
# 在这混乱之中，我学会了如何生存，也学会了如何保护自己。我与几个要好的朋友组成了小团体。我们彼此扶持，共同面对校园里的各种挑战，形成了一种“团结对外”的默契。我的一个好友，就因为卷入打架事件，最终被父母领回沈阳。即便如此，我们之间的友谊也未曾中断，直到现在我们依然保持着联系，前段时间他还邀请我当他的伴郎。这段经历让我认识到，在逆境中，友谊和团结的力量是多么重要。
# 初中这段经历，对我性格的塑造产生了深远的影响。它让我过早地接触到了社会复杂的一面，也让我认识到自己身上“意气用事”的一面。在那个年纪，面对不公或挑衅，我常常会冲动行事。这种“意气用事”的特质，在后来的很长一段时间里都伴随着我。直到上大学，我才慢慢意识到这个问题，并逐渐开始修正。我不太清楚具体是怎么改的，就是逐渐地、慢慢地意识到了问题，然后慢慢地就改过来了。现在的我，在面对问题时，会更加理智地去判断。
# 回首那段岁月，我为自己能够坚持到毕业而感到庆幸。在许多同学中途辍学的大背景下，其中就包括我的朋友张望,
# 我的坚持，不仅是对学业的执着，更是对未来的一种信念。这段混乱而又充满挑战的初中生活，磨砺了我的意志，锻炼了我的环境适应能力，也奠定了我坚韧的性格底色。它让我明白，无论身处何种困境，只要心中有目标，并为之不懈努力，便能找到属于自己的出路。
# """
#     result = extract_person_place(bio_chunk)
#     print(result)


from fastapi.testclient import TestClient
# Pytest fixture 来提供 TestClient 实例
# `yield` 关键字用于在测试 setup/teardown 期间执行一些操作
# 这里，我们用它来在每个测试前重置模拟数据库
import pytest
from diglife.server.__main__ import app

@pytest.fixture(name="client") # 为fixture起一个别名，方便测试函数调用
def client_fixture():
    """
    一个 Pytest fixture，提供 FastAPI TestClient 实例。
    在每个测试用例运行前，会重置模拟数据库，确保测试隔离。
    """
    # # 每次测试前，重置数据库到初始状态
    # initial_db = {
    #     "foo": {"name": "Foo", "price": 50.2},
    #     "bar": {"name": "Bar", "price": 62.0},
    # }
    # items_db.clear() # 清空当前数据库
    # items_db.update(initial_db) # 恢复到初始数据

    with TestClient(app) as client:
        yield client # 返回 TestClient 实例供测试函数使用

# --- 测试用例 ---

def test_read_root(client: TestClient):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LLM Service is running."}

def test_life_topic_score(client: TestClient):
    """人生主题分值"""
    data = {
            "S_list": [7, 8, 9, 10],
            "K": 0.3,
            "total_score": 0,
            "epsilon": 0.0001
            }
    response = client.post("/life_topic_score/", json=data)
    assert response.status_code == 200
    assert response.json().get("message") == "Life topic score calculated successfully"
    score = response.json().get("result") 
    assert 0< score <100

    assert isinstance(score,int)


def test_life_aggregate_scheduling_score(client: TestClient):
    """人生总进度分值计算"""
    data = {
            "S_list": [54, 98, 89, 45, 94, 89, 44],
            "K": 0.03,
            "total_score": 0,
            "epsilon": 0.0001
            }
    response = client.post("/life_aggregate_scheduling_score/", json=data)
    assert response.status_code == 200
    assert response.json().get("message") == "life aggregate scheduling score successfully"
    score = response.json().get("result") 
    assert 0< score <100
    assert isinstance(score,float)


def test_memory_card_score(client: TestClient):
    """测试创建新商品"""
    data = {
        "memory_cards": ['我出生在东北辽宁葫芦岛下面的一个小村庄。小时候，那里的生活比较简单，人们日出而作，日落而息，生活节奏非常有规律，也非常美好。当时我们都是山里的野孩子，没有什么特别的兴趣爱好，就在山里各种疯跑。我小时候特别喜欢晚上看星星，那时的夜晚星星非常多，真的是那种突然就能看到漫天繁星的感觉。',
 '在我高中的时候，我对天文物理和理论物理就非常感兴趣。我当时高中是在我们县城里读的，资源没有那么丰富，我们所有的精力都放在学科的学习上。',
 '离开泸沽湖之后，我和我的义工搭子一起去了虎跳峡徒步。在徒步过程中，我们还看到了日照金山。当时我们徒步到半山腰的一个临时扎点时，正好看到这个美景，非常激动地拍了照。能在徒步途中遇到这样的美景，确实让人兴奋不已。在虎跳峡徒步之后，我们在丽江休整了一天，然后就各自前往下一个目的地了。',
 '我第一份职业是产品经理，当时在国内一家做专网通信的龙头企业。目前我是一位AI产品经理。',
 '我记得在我小的时候，大概是在我三四年级的时候，我和我的小伙伴一块去上山抓蝎子。小时候那会儿都比较皮，到处跑。我在山上去翻蝎子的时候，遇到了一条蛇！我和它对视过后，我就慌忙地转身逃跑。在我刚转身逃跑的时候，我看见山上的小路上有一个树枝倒下来了，倒在我的前面，然后我就跳了起来。在我跳起来的时候，那条蛇就在我的脚底下钻过去了，当时真的吓得我很害怕。如果不是那个树枝的话，我可能就被咬了。而且那条蛇，我记得它是三角脑袋，枯草色的，看着像是有毒的样子。之后我对山上有些阴影了，都不怎么去上山抓蝎子了。我现在上山还是会拿根棍子，到处敲一敲！说实话，真的有阴影。',
 '我在凉山州做项目期间，曾替客户背过一次“黑锅”。那次是我们接处警的项目刚刚上线，因为项目是在凉山州做的，所以我们在西昌市驻扎。当地有两个公安局，一个是州公安局，一个是市公安局。上线当天，我们原定在州公安局开新闻发布会，市公安局这边会同步进行。但就在当天早上，我被客户叫到了市公安局，本该去参加发布会的我被临时调动。客户告诉我，市公安局的大领导、局长可能会来问些问题，让我再去给他讲讲我们的系统。于是我直接去了市公安局，没有去参加发布会。\n\n当时叫我去的是客户那边的对接人，一位指挥长。在他们开新闻发布会的时候，我们就在后面聊天，并给他讲一些系统的事情，因为我们关系都比较熟了。发布会结束后，公安局的局长说要让我调一份接警的录音出来。这事儿是因为他们下面有一个派出所警员在接警过程中，对接警员的态度不好，局长比较生气，说要调出证据去处罚他，认为他既然对自己的同志态度都不好，那对待民众的态度肯定会更不好。他只要那份录音文件，让我从我们的系统里导出来。\n\n局长要在他们全市的公安局领导面前播放这份录音，但是他们播放的设备不能直接登录我们的系统，所以我需要把录音文件导出来，再插到他们播放的电脑上去播放。我找到U盘后，因为我在那块待的时间比较长，比较熟，就想把音频文件直接导到他们的电脑上，然后播放出来。结果，他们的电脑比较老旧，U盘识别不了，没有驱动，导致播放不了。我尝试了各种方法也不行。就在这时，局长本来就在气头上，他更生气了。他一开始以为我是他们局内的人，是信息部的，就冲我发了脾气，说我办事不力，问我是哪个部门的。我告诉他，我是这个系统公司的人，不是他们公安局的人。\n\n局长当时已经放出话来，他说我们的系统做的不好，不能直接播放录音，但其实是能播放的，只不过是他们自己内部系统的一些问题。我想解释，但局长没有给我解释的机会，他就在那里一直守着，在所有公安局的人面前指着我的鼻子数落我，还让我把我的领导叫来。他甚至说，如果系统做得不好，可以不采用我们的系统。我当时内心并没有太多感受，因为我知道这不是我的问题，我只是替他们背了一个锅而已。后来他们的人接手了，开始处理他们电脑的问题。局长也发现是他们的人一直在处理问题，也意识到了是他们自己的问题，跟我们没关系。但他还是把我们的领导叫来了。在这个过程中，我们客户，也就是公安局的那个主任，还在旁边小声安慰我说：“没事没事，领导发完火就过去了。”其实我内心是不在乎的。\n\n我的领导也很懵，因为他们正在那边开新闻发布会，突然把我的领导，还有公安局和我对接的那些负责人都叫来了。他们以为出了什么问题，大领导发大火。他们比较懵，但是叫来之后，局长也没有说什么，说了一些无关紧要的东西，做了一些指示。就这样，我默默地背了一个锅。这件事情对我的工作选择没有什么影响，因为我知道这不是我的问题，领导们也知道我只是背了一个锅，这事就这么过去了。能被局长兼副市长指着鼻子骂，对我来说也是一种特殊的体验']
        }
    response = client.post("/memory_card/score", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    assert isinstance(result,list)
    for i in result:
        score = i.get("score")
        assert 0<= score <=10
        assert isinstance(score,int)


# 
def test_memory_card_score_by_successfil_radio():
    """
    测试加法函数，并计算内部测试用例的通过比例。
    注意：这会使 pytest 将整个函数视为一个测试，
    而不是为每个数据组生成独立的测试报告。
    """
    # 这里定义通过阈值, 高于该比例则通过
    MIN_SUCCESS_RATE = 00.0 
    
    # 这里定义数据
    test_cases = [
        (1, 2, 3),      # Pass
        (-1, 1, 0),     # Pass
        (0, 0, 0),      # Pass
        (100, 200, None), # Fail
        (-5, -3, -8)    # Pass
    ]

    # 这里定义断言
    def add(input_a,input_b,expected_sum):
        assert expected_sum == input_a + input_b + 1


    successful_assertions = 0
    total_assertions = len(test_cases)
    failed_cases = []

    for i, (input_a, input_b, expected_sum) in enumerate(test_cases):
        try:
            # 这里将参数传入
            add(input_a,input_b,expected_sum)
            successful_assertions += 1
        except AssertionError as e:
            failed_cases.append(f"Case {i+1} ({input_a}+{input_b}): FAILED. Expected {expected_sum},. Error: {e}")
        except Exception as e: # 捕获其他可能的错误
            failed_cases.append(f"Case {i+1} ({input_a}+{input_b}): ERROR. Input {input_a},{input_b}. Error: {e}")
            print(f"Case {i+1} ({input_a}+{input_b}): ERROR. Input {input_a},{input_b}. Error: {e}")

    success_rate = (successful_assertions / total_assertions) * 100
    print(f"\n--- Aggregated Results ---")
    print(f"Total test cases: {total_assertions}")
    print(f"Successful cases: {successful_assertions}")
    print(f"Failed cases count: {len(failed_cases)}")
    print(f"Success Rate: {success_rate:.2f}%")

    assert success_rate >= MIN_SUCCESS_RATE, \
        f"Test failed: Success rate {success_rate:.2f}% is below required {MIN_SUCCESS_RATE:.2f}%." + \
        f"\nFailed cases details:\n" + "\n".join(failed_cases)







def test_memory_card_merge(client: TestClient):
    """测试创建新商品"""
    data = {
            "memory_cards": [
                "这是一个关于FastAPI的记忆卡片。",
                "FastAPI是一个现代、快速（高性能）的web框架。",
                "它基于Python 3.7+标准类型提示。"
            ]
            }
    response = client.post("/memory_card/merge", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    assert isinstance(result,str)

def test_memory_card_polish(client: TestClient):
    """测试创建新商品"""
    data = {
        "memory_cards": [
            "这是一个关于FastAPI的记忆卡片。",
            "FastAPI是一个现代、快速（高性能）的web框架。",
            "它基于Python 3.7+标准类型提示。"
        ]
        }
    response = client.post("/memory_card/polish", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    print(result)
    assert isinstance(result,list)
    assert len(result) == len(data.get("memory_cards"))



def test_memory_card_generate_by_text(client: TestClient):
    """测试创建新商品"""
    data = {
    "text": "ai:柴东升，你好呀。初中那段不太顺利的经历，你愿意和我详细说说吗？\nhuman:初中没有不太顺利，在我的记忆中，初中还是挺快乐的。\nai:那真是太好了。在学校与同学们一起学习、玩耍，肯定发生了很多让你难以忘怀的趣事吧？\nhuman:对的，虽然初中那会儿学校比较乱，但是和朋友在一起还是很快乐的。\nai:学校环境乱，会影响到你吗？你的朋友都是些什么样的人呢？\nhuman:和我玩的比较好的朋友都是学习不太好的人。 因为我的性格，怎么说在初中的时候也是也不是那种一心葡萄学习上的，我也会和他们一块出去玩，一块出去疯。 只不过是该学习时候的学习，该班的时候就玩。\nai:懂得劳逸结合，这是很难得的呀。那你和朋友们一般都去哪里玩呢？\nhuman:当时就是去到县里的街上去，到处溜达，嗯，到处逛，然后跟他们在一块打打闹闹的。\nai:听起来很有意思呢。那时候的时光一定很美好吧？有没有什么特别的经历呢？\nhuman:给我印象最深刻的是初三的时候，当时我们嗯刚病校。 我另一个学校刚和您在一块，然后因为初中那会学生都属于青春期，比较躁动。嗯，有一次在。 我们中午吃饭的时候，嗯，我们班上和我关系很好的一个人。 另一个学校的一个人在打饭的时候嗯争执起来，打了起来，然后最后嗯变成了我们两个。 班的人的一个。 混战打勋章，然后当时我也加入到其中了。嗯，我的头脑袋。 不知道被从哪飞来的一个餐牌给打中了。 当时还起了一个浩大的包裹。\nai:混战？那场面一定很混乱吧。被餐牌打中脑袋，有没有去看医生呢？\nhuman:没有，就是鼓了一个包，当时也比较皮，没有那么脆弱，过两天你就没事了，然后这场请假。 导致了我那个朋友被他父母领回去了，因为他父母是他家是在沈阳。嗯。 然后但是把它放到了老家来上学，但是经历过这个事情之后，他父母就把他领回沈阳了。\nai:当时年少轻狂，大家都容易冲动。那后来呢？你们还有联系吗？\nhuman:有他有联系的，前段时间他结婚，嗯，我他邀请我去给他当伴郎，但是我因为工作比较忙没有去上。\nai:时光飞逝，当年的少年如今都已结婚生子。那你现在对当年的那场混战有什么看法呢？\nhuman:没有什么，就是当时都比较小，又是青春期，大家都比较冲动。\nai:是啊，谁的青春不冲动呢？那你觉得这段经历对你的成长有什么影响吗？\nhuman:其实初中的那段经历让我在之后很长的一段时间都会比较意气用事。\nai:看来年少时的经历，多少会在我们身上留下些痕迹。那后来呢？你是怎么意识到这个问题的？\nhuman:是在上大学的时候慢慢的意识到这个问题，并且。 主播改过来了！\nai:大学是个成长的好阶段。那你是通过什么方式改掉意气用事这个习惯的呢？\nhuman:我也不太清楚，就是逐渐的慢慢的意识到这个问题，然后慢慢的就。 改过来了！\nai:能自我觉察并做出改变，这很了不起。那现在的你，在面对问题时，会更加理智冷静吧？\nhuman:是的，现在我回很理智的去判断。\n"
    }
    response = client.post("/memory_card/generate_by_text", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    assert isinstance(result,list)

def test_memory_card_generate(client: TestClient):
    """测试创建新商品"""
    data = {
    "text": "ai:柴东升，你好呀。初中那段不太顺利的经历，你愿意和我详细说说吗？\nhuman:初中没有不太顺利，在我的记忆中，初中还是挺快乐的。\nai:那真是太好了。在学校与同学们一起学习、玩耍，肯定发生了很多让你难以忘怀的趣事吧？\nhuman:对的，虽然初中那会儿学校比较乱，但是和朋友在一起还是很快乐的。\nai:学校环境乱，会影响到你吗？你的朋友都是些什么样的人呢？\nhuman:和我玩的比较好的朋友都是学习不太好的人。 因为我的性格，怎么说在初中的时候也是也不是那种一心葡萄学习上的，我也会和他们一块出去玩，一块出去疯。 只不过是该学习时候的学习，该班的时候就玩。\nai:懂得劳逸结合，这是很难得的呀。那你和朋友们一般都去哪里玩呢？\nhuman:当时就是去到县里的街上去，到处溜达，嗯，到处逛，然后跟他们在一块打打闹闹的。\nai:听起来很有意思呢。那时候的时光一定很美好吧？有没有什么特别的经历呢？\nhuman:给我印象最深刻的是初三的时候，当时我们嗯刚病校。 我另一个学校刚和您在一块，然后因为初中那会学生都属于青春期，比较躁动。嗯，有一次在。 我们中午吃饭的时候，嗯，我们班上和我关系很好的一个人。 另一个学校的一个人在打饭的时候嗯争执起来，打了起来，然后最后嗯变成了我们两个。 班的人的一个。 混战打勋章，然后当时我也加入到其中了。嗯，我的头脑袋。 不知道被从哪飞来的一个餐牌给打中了。 当时还起了一个浩大的包裹。\nai:混战？那场面一定很混乱吧。被餐牌打中脑袋，有没有去看医生呢？\nhuman:没有，就是鼓了一个包，当时也比较皮，没有那么脆弱，过两天你就没事了，然后这场请假。 导致了我那个朋友被他父母领回去了，因为他父母是他家是在沈阳。嗯。 然后但是把它放到了老家来上学，但是经历过这个事情之后，他父母就把他领回沈阳了。\nai:当时年少轻狂，大家都容易冲动。那后来呢？你们还有联系吗？\nhuman:有他有联系的，前段时间他结婚，嗯，我他邀请我去给他当伴郎，但是我因为工作比较忙没有去上。\nai:时光飞逝，当年的少年如今都已结婚生子。那你现在对当年的那场混战有什么看法呢？\nhuman:没有什么，就是当时都比较小，又是青春期，大家都比较冲动。\nai:是啊，谁的青春不冲动呢？那你觉得这段经历对你的成长有什么影响吗？\nhuman:其实初中的那段经历让我在之后很长的一段时间都会比较意气用事。\nai:看来年少时的经历，多少会在我们身上留下些痕迹。那后来呢？你是怎么意识到这个问题的？\nhuman:是在上大学的时候慢慢的意识到这个问题，并且。 主播改过来了！\nai:大学是个成长的好阶段。那你是通过什么方式改掉意气用事这个习惯的呢？\nhuman:我也不太清楚，就是逐渐的慢慢的意识到这个问题，然后慢慢的就。 改过来了！\nai:能自我觉察并做出改变，这很了不起。那现在的你，在面对问题时，会更加理智冷静吧？\nhuman:是的，现在我回很理智的去判断。\n"
    }
    response = client.post("/memory_card/generate/", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    assert isinstance(result,list)


##

def test_generate_biography_free(client: TestClient):
    """测试创建新商品"""
    data = {
    "text": "ai:柴东升，你好呀。初中那段不太顺利的经历，你愿意和我详细说说吗？\nhuman:初中没有不太顺利，在我的记忆中，初中还是挺快乐的。\nai:那真是太好了。在学校与同学们一起学习、玩耍，肯定发生了很多让你难以忘怀的趣事吧？\nhuman:对的，虽然初中那会儿学校比较乱，但是和朋友在一起还是很快乐的。\nai:学校环境乱，会影响到你吗？你的朋友都是些什么样的人呢？\nhuman:和我玩的比较好的朋友都是学习不太好的人。 因为我的性格，怎么说在初中的时候也是也不是那种一心葡萄学习上的，我也会和他们一块出去玩，一块出去疯。 只不过是该学习时候的学习，该班的时候就玩。\nai:懂得劳逸结合，这是很难得的呀。那你和朋友们一般都去哪里玩呢？\nhuman:当时就是去到县里的街上去，到处溜达，嗯，到处逛，然后跟他们在一块打打闹闹的。\nai:听起来很有意思呢。那时候的时光一定很美好吧？有没有什么特别的经历呢？\nhuman:给我印象最深刻的是初三的时候，当时我们嗯刚病校。 我另一个学校刚和您在一块，然后因为初中那会学生都属于青春期，比较躁动。嗯，有一次在。 我们中午吃饭的时候，嗯，我们班上和我关系很好的一个人。 另一个学校的一个人在打饭的时候嗯争执起来，打了起来，然后最后嗯变成了我们两个。 班的人的一个。 混战打勋章，然后当时我也加入到其中了。嗯，我的头脑袋。 不知道被从哪飞来的一个餐牌给打中了。 当时还起了一个浩大的包裹。\nai:混战？那场面一定很混乱吧。被餐牌打中脑袋，有没有去看医生呢？\nhuman:没有，就是鼓了一个包，当时也比较皮，没有那么脆弱，过两天你就没事了，然后这场请假。 导致了我那个朋友被他父母领回去了，因为他父母是他家是在沈阳。嗯。 然后但是把它放到了老家来上学，但是经历过这个事情之后，他父母就把他领回沈阳了。\nai:当时年少轻狂，大家都容易冲动。那后来呢？你们还有联系吗？\nhuman:有他有联系的，前段时间他结婚，嗯，我他邀请我去给他当伴郎，但是我因为工作比较忙没有去上。\nai:时光飞逝，当年的少年如今都已结婚生子。那你现在对当年的那场混战有什么看法呢？\nhuman:没有什么，就是当时都比较小，又是青春期，大家都比较冲动。\nai:是啊，谁的青春不冲动呢？那你觉得这段经历对你的成长有什么影响吗？\nhuman:其实初中的那段经历让我在之后很长的一段时间都会比较意气用事。\nai:看来年少时的经历，多少会在我们身上留下些痕迹。那后来呢？你是怎么意识到这个问题的？\nhuman:是在上大学的时候慢慢的意识到这个问题，并且。 主播改过来了！\nai:大学是个成长的好阶段。那你是通过什么方式改掉意气用事这个习惯的呢？\nhuman:我也不太清楚，就是逐渐的慢慢的意识到这个问题，然后慢慢的就。 改过来了！\nai:能自我觉察并做出改变，这很了不起。那现在的你，在面对问题时，会更加理智冷静吧？\nhuman:是的，现在我回很理智的去判断。\n"
    }
    response = client.post("/generate_biography_free/", json=data)
    assert response.status_code == 200
    
    assert response.json().get('result')
    result = response.json().get('result')
    assert isinstance(result,str)


## 
def test_generate_biography(client: TestClient):
    """测试创建新商品"""
    data = {
            "vitae": "张三，男，1980年出生于北京，清华大学计算机系毕业，曾任职于Google、百度，现为某AI公司首席科学家。",
            "memory_cards": [
                "张三在大学期间曾参与ACM国际大学生程序设计竞赛并获奖。",
                "张三在Google主导开发了XXX搜索引擎核心算法。",
                "张三在百度负责AI大模型研发，推动了YYY项目的成功落地。",
                "张三热衷于公益事业，多次捐款资助贫困学生。"
            ]
            }
    response = client.post("/generate_biography/", json=data)
    assert response.status_code == 200
    
    assert response.json()
    task_id = response.json().get("task_id")
    status = response.json().get("status")
    
    assert task_id is not None 
    assert isinstance(task_id,str)
    assert status == "PENDING"

    response = client.get(f"/get_biography_result/{task_id}")
    assert response.status_code == 200

def test_read_item_existing(client: TestClient):
    """测试获取存在的商品"""
    response = client.get("/items/foo")
    assert response.status_code == 200
    assert response.json() == {"name": "Foo", "price": 50.2}

def test_read_item_not_found(client: TestClient):
    """测试获取不存在的商品"""
    response = client.get("/items/baz")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_update_item_existing(client: TestClient):
    """测试更新存在的商品"""
    response = client.put(
        "/items/foo",
        json={"name": "Foo Updated", "price": 60.0, "is_offer": True}
    )
    assert response.status_code == 200
    assert response.json() == {"item_id": "foo", "name": "Foo Updated", "price": 60.0, "is_offer": True}
    
    # 验证数据库是否实际更新
    response_get = client.get("/items/foo")
    assert response_get.json()["name"] == "Foo Updated"

def test_update_item_not_found(client: TestClient):
    """测试更新不存在的商品"""
    response = client.put(
        "/items/baz",
        json={"name": "Baz", "price": 10.0}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_create_item(client: TestClient):
    """测试创建新商品"""
    new_item_data = {"name": "New Item", "price": 100.0, "is_offer": False}
    response = client.post("/items/", json=new_item_data)
    assert response.status_code == 201
    assert response.json() == new_item_data
    
    # 验证数据库中是否存在该商品
    response_get = client.get("/items/new-item")
    assert response_get.status_code == 200
    assert response_get.json()["name"] == "New Item"

def test_create_item_conflict(client: TestClient):
    """测试创建已存在的商品（冲突）"""
    existing_item_data = {"name": "Foo", "price": 70.0} # "foo" 已经存在
    response = client.post("/items/", json=existing_item_data)
    assert response.status_code == 409
    assert response.json() == {"detail": "Item with this name already exists"}

def test_delete_item_existing(client: TestClient):
    """测试删除存在的商品"""
    response = client.delete("/items/bar")
    assert response.status_code == 204
    assert response.text == "" # 对于 204 No Content，响应体通常是空的

    # 验证商品是否已被删除
    response_get = client.get("/items/bar")
    assert response_get.status_code == 404

def test_delete_item_not_found(client: TestClient):
    """测试删除不存在的商品"""
    response = client.delete("/items/non-existent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

# 测试只更新部分字段
def test_partial_update_item(client: TestClient):
    response = client.put(
        "/items/foo",
        json={"price": 75.5} # 只更新价格
    )
    assert response.status_code == 200
    assert response.json() == {"item_id": "foo", "name": "Foo", "price": 75.5} # name 应该保持不变
    
    response_get = client.get("/items/foo")
    assert response_get.json()["price"] == 75.5
    assert response_get.json()["name"] == "Foo" # 验证 name 没有改变