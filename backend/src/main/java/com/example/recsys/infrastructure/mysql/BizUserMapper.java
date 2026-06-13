package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.recsys.domain.entity.BizUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface BizUserMapper extends BaseMapper<BizUser> {

    /**
     * 管理员后台分页, 联 biz_user_role 一次性按角色过滤,
     * 避免 Java 端二次过滤导致 total 不准.
     */
    Page<BizUser> selectAdminPage(Page<BizUser> page,
                                  @Param("keyword") String keyword,
                                  @Param("status") Integer status,
                                  @Param("roleCode") String roleCode);
}
