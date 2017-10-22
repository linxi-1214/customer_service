INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (1,'#','系统设置',0,'fa-cog',1);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (2,'menu_index','菜单管理',1,'fa-list-alt',2);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (3,'#','玩家管理',0,'fa-gamepad',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (4,'player_index','我的玩家',3,'fa-gamepad',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (5,'import_player','玩家导入',3,'fa-sign-in  ',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (6,'contract_player','联系玩家',3,'fa-phone-square',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (7,'role_index','角色管理',1,'fa-sitemap',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (8,'result_index','联系结果',1,'fa-thumb-tack',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (9,'user_index','用户管理',1,'fa-user',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (10,'game_index','游戏管理',1,'fa-bug',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (11,'#','工作报告',0,'fa-windows',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (12,'user_report','客服报告',11,'',NULL);
INSERT INTO `menu` (`id`,`name`,`label`,`parent`,`icon`,`order_index`) VALUES (13,'player_contact_detail','玩家详情',11,'',NULL);


INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (1,'已查看',0,0,1);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (2,'空号',0,0,2);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (3,'玩家挂断',0,0,2);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (4,'暂时无法接通',0,0,2);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (5,'无人接听',0,0,2);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (6,'接听但无反馈',0,0,3);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (7,'玩家另约时间',0,0,3);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (8,'关机',0,0,2);
INSERT INTO `contract_result` (`id`,`result`,`bind`,`show`,`process`) VALUES (9,'联系成功',1,0,4);


INSERT INTO `role` (`id`,`name`,`desc`) VALUES (1,'admin','管理员');
INSERT INTO `role` (`id`,`name`,`desc`) VALUES (2,'data user','数据管理员');
INSERT INTO `role` (`id`,`name`,`desc`) VALUES (3,'service','客服人员');


INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (1,1,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (2,2,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (3,3,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (5,4,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (6,5,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (9,6,3);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (10,6,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (11,6,2);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (12,7,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (13,8,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (14,9,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (15,10,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (16,11,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (17,12,1);
INSERT INTO `role_bind_menu` (`id`,`menu_id`,`role_id`) VALUES (18,13,1);