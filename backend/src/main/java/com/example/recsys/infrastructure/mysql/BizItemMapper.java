package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.recsys.domain.entity.BizItem;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizItemMapper extends BaseMapper<BizItem> {}
