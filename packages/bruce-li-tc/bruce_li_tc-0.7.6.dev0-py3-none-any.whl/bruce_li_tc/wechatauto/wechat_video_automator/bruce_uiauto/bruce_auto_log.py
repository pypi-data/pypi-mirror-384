# wechatauto/wechat_video_automator/bruce_uiauto/bruce_auto_log.py
from loguru import logger

# 使用 .bind() 方法创建带有固定标识的日志器
# 键名 "library_name" 是与其他库和主项目约定的标识符
#library_logger = logger
library_logger = logger.bind(library_name="bruce_uiauto")