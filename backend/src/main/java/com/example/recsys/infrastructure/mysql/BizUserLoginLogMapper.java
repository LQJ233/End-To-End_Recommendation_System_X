package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.recsys.domain.entity.BizUserLoginLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizUserLoginLogMapper extends BaseMapper<BizUserLoginLog> {}
