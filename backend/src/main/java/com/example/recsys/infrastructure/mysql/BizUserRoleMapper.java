package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.recsys.domain.entity.BizUserRole;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizUserRoleMapper extends BaseMapper<BizUserRole> {}
