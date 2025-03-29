from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
1113734
1112212
582097
1070724
1100601
1101870
1094997
526075
1096727
1097693
1082841
1046190
1076777
1076856
1073331
1074766
31268
1067711
536739
1051375
1059716
1049542
606305
1045158
1041360
1035600
1037471
1034459
1035109
1035563
1015878
1027429
1023124
1023190
1023025
1020602
1020921
1020575
1020321
1018362
1019714
1019843
1019571
1016618
523623
1015371
1014473
610053
649275
651485
651923
525442
645810
545020
643139
403905
643627
642254
231551
481727
331325
142576
633986
618822
615404
627921
623652
624045
623162
622472
619560
619522
617834
616949
615421
408092
613935
613933
611627
573029
548802
601776
601737
277246
299147
368814
411638
415657
271426
272472
532780
531545
556082
567000
573202
254244
568711
300497
597920
597784
391185
594876
592047
592344
592354
467275
61934
589687
301140
584448
583203
578538
571627
579276
577559
575814
574867
575184
572345
573526
573527
571964
571965
572488
572336
569114
553357
523283
570146
570197
569561
570081
355330
543331
568741
544658
567152
562239
561689
556585
554128
190449
529585
545532
545960
548957
549199
549296
541815
531549
423764
539483
540698
495851
303307
527698
515859
522064
521654
498891
505233
205748
303070
243900
1016841
514493
515591
385781
515346
515092
480839
1016846
511586
513615
513647
451594
511569
285991
509693
114802
505690
466657
245302
504974
502161
500514
500680
497729
140064
265424
265520
386470
415010
279841
27832
420288
480575
496106
198146
284596
204303
482774
485735
419684
476477
117001
420961
422413
425069
425204
188159
460611
476951
223591
472633
290897
255606
248326
294247
118777
378637
487305
486082
77315
113403
468912
21135
481314
484812


'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
