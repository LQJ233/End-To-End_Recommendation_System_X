package com.example.recsys.infrastructure.mysql;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.recsys.domain.entity.RecRequestSnapshot;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface RecRequestSnapshotMapper extends BaseMapper<RecRequestSnapshot> {}
