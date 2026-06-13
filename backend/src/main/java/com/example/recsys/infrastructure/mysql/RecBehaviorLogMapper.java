package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.recsys.domain.entity.RecBehaviorLog;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface RecBehaviorLogMapper extends BaseMapper<RecBehaviorLog> {
    int batchInsert(@Param("list") List<RecBehaviorLog> list);
}
