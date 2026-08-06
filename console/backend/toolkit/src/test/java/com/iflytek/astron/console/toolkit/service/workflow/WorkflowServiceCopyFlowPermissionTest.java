package com.iflytek.astron.console.toolkit.service.workflow;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.iflytek.astron.console.commons.constant.ResponseEnum;
import com.iflytek.astron.console.commons.entity.workflow.Workflow;
import com.iflytek.astron.console.commons.exception.BusinessException;
import com.iflytek.astron.console.commons.util.space.SpaceInfoUtil;
import com.iflytek.astron.console.toolkit.tool.DataPermissionCheckTool;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class WorkflowServiceCopyFlowPermissionTest {

    @Mock
    private DataPermissionCheckTool dataPermissionCheckTool;

    private WorkflowService workflowService;

    @BeforeEach
    void setUp() {
        workflowService = spy(new WorkflowService());
        ReflectionTestUtils.setField(workflowService, "dataPermissionCheckTool", dataPermissionCheckTool);
    }

    @Test
    void copyFlowShouldCheckSourceVisibilityAndTargetOwnership() {
        Workflow source = workflow("source", 100L, "source-data");
        Workflow target = workflow("target", 100L, "target-data");
        doReturn(source, target).when(workflowService).getOne(any(Wrapper.class));
        doReturn(true).when(workflowService).updateById(target);

        try (MockedStatic<SpaceInfoUtil> space = org.mockito.Mockito.mockStatic(SpaceInfoUtil.class)) {
            space.when(SpaceInfoUtil::getSpaceId).thenReturn(100L);
            assertThat(workflowService.copyFlow("source", "target")).isEqualTo(true);
        }

        verify(dataPermissionCheckTool).checkWorkflowVisible(source, 100L);
        verify(workflowService).updateById(target);
        assertThat(target.getData()).isEqualTo("source-data");
    }

    @Test
    void copyFlowShouldNotDiscloseInvisibleSource() {
        Workflow source = workflow("source", 200L, "secret-data");
        Workflow target = workflow("target", 100L, "target-data");
        doReturn(source, target).when(workflowService).getOne(any(Wrapper.class));
        doThrow(new BusinessException(ResponseEnum.INSUFFICIENT_PERMISSIONS))
                .when(dataPermissionCheckTool).checkWorkflowVisible(source, 100L);

        try (MockedStatic<SpaceInfoUtil> space = org.mockito.Mockito.mockStatic(SpaceInfoUtil.class)) {
            space.when(SpaceInfoUtil::getSpaceId).thenReturn(100L);
            assertThatThrownBy(() -> workflowService.copyFlow("source", "target"))
                    .isInstanceOf(BusinessException.class);
        }

        verify(workflowService, never()).updateById(any(Workflow.class));
        assertThat(target.getData()).isEqualTo("target-data");
    }

    @Test
    void copyFlowShouldNotOverwriteTargetFromAnotherSpace() {
        Workflow source = workflow("source", 100L, "source-data");
        Workflow target = workflow("target", 200L, "target-data");
        target.setIsPublic(true);
        doReturn(source, target).when(workflowService).getOne(any(Wrapper.class));

        try (MockedStatic<SpaceInfoUtil> space = org.mockito.Mockito.mockStatic(SpaceInfoUtil.class)) {
            space.when(SpaceInfoUtil::getSpaceId).thenReturn(100L);
            assertThatThrownBy(() -> workflowService.copyFlow("source", "target"))
                    .isInstanceOf(BusinessException.class)
                    .extracting("code")
                    .isEqualTo(ResponseEnum.INSUFFICIENT_PERMISSIONS.getCode());
        }

        verify(dataPermissionCheckTool).checkWorkflowVisible(source, 100L);
        verify(workflowService, never()).updateById(any(Workflow.class));
        assertThat(target.getData()).isEqualTo("target-data");
    }

    private Workflow workflow(String flowId, Long spaceId, String data) {
        Workflow workflow = new Workflow();
        workflow.setFlowId(flowId);
        workflow.setSpaceId(spaceId);
        workflow.setData(data);
        return workflow;
    }
}
