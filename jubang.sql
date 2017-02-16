/*
Navicat MySQL Data Transfer

Source Server         : localhost
Source Server Version : 50711
Source Host           : 127.0.0.1:3306
Source Database       : jubang

Target Server Type    : MYSQL
Target Server Version : 50711
File Encoding         : 65001

Date: 2017-02-16 16:24:58
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `add_mp_list`
-- ----------------------------
DROP TABLE IF EXISTS `add_mp_list`;
CREATE TABLE `add_mp_list` (
  `_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `name` varchar(50) DEFAULT '' COMMENT '要添加的公众号名称',
  `wx_hao` varchar(50) DEFAULT '' COMMENT '公众号的微信号',
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of add_mp_list
-- ----------------------------

-- ----------------------------
-- Table structure for `mp_info`
-- ----------------------------
DROP TABLE IF EXISTS `mp_info`;
CREATE TABLE `mp_info` (
  `_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `name` varchar(50) DEFAULT '' COMMENT '公众号名称',
  `wx_hao` varchar(20) DEFAULT '' COMMENT '公众号的微信号',
  `company` varchar(100) DEFAULT '' COMMENT '主体名称',
  `description` varchar(200) DEFAULT '' COMMENT '功能简介',
  `logo_url` varchar(200) DEFAULT '' COMMENT 'logo url',
  `qr_url` varchar(200) DEFAULT '' COMMENT '二维码URL',
  `create_time` datetime DEFAULT NULL COMMENT '加入牛榜时间',
  `update_time` datetime DEFAULT NULL COMMENT '最后更新时间',
  `rank_article_release_count` int(11) DEFAULT '0' COMMENT '群发次数',
  `rank_article_count` int(11) DEFAULT '0' COMMENT '群发篇数',
  `last_qunfa_id` int(30) DEFAULT '0' COMMENT '最后的群发ID',
  `last_qufa_time` datetime DEFAULT NULL COMMENT '最后一次群发的时间',
  `wz_url` varchar(300) DEFAULT '' COMMENT '最近文章URL',
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB AUTO_INCREMENT=266 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of mp_info
-- ----------------------------

-- ----------------------------
-- Table structure for `wenzhang_info`
-- ----------------------------
DROP TABLE IF EXISTS `wenzhang_info`;
CREATE TABLE `wenzhang_info` (
  `_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `title` varchar(100) DEFAULT '' COMMENT '文章标题',
  `source_url` varchar(300) DEFAULT '' COMMENT '原文地址',
  `cover_url` varchar(200) DEFAULT '' COMMENT '封面图URL',
  `description` varchar(200) DEFAULT '' COMMENT '文章摘要',
  `date_time` datetime DEFAULT NULL COMMENT '文章推送时间',
  `mp_id` int(11) DEFAULT '0' COMMENT '对应的公众号ID',
  `read_count` int(11) DEFAULT '0' COMMENT '阅读数',
  `like_count` int(11) DEFAULT '0' COMMENT '点攒数',
  `comment_count` int(11) DEFAULT '0' COMMENT '评论数',
  `content_url` varchar(300) DEFAULT '' COMMENT '文章永久地址',
  `author` varchar(50) DEFAULT '' COMMENT '作者',
  `msg_index` int(11) DEFAULT '0' COMMENT '一次群发中的图文顺序 1是头条 ',
  `copyright_stat` int(1) DEFAULT '0' COMMENT '1表示原创 0表示非原创',
  `qunfa_id` int(30) DEFAULT '0' COMMENT '群发消息ID',
  `type` int(11) DEFAULT '0' COMMENT '消息类型',
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6559 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of wenzhang_info
-- ----------------------------

-- ----------------------------
-- Table structure for `wenzhang_statistics`
-- ----------------------------
DROP TABLE IF EXISTS `wenzhang_statistics`;
CREATE TABLE `wenzhang_statistics` (
  `_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `wz_id` int(11) DEFAULT '0' COMMENT '对应的文章ID',
  `create_time` datetime DEFAULT NULL COMMENT '统计时间',
  `read_count` int(11) DEFAULT '0' COMMENT '新增阅读数',
  `like_count` int(11) DEFAULT '0' COMMENT '新增点攒数',
  `comment_count` int(11) DEFAULT '0' COMMENT '新增评论数',
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4006 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of wenzhang_statistics
-- ----------------------------
