use crate::qir::{
    emit_qis_gate, emit_qis_gate_finish, emit_qis_measure_to_result, emit_qis_qalloc,
    emit_qis_qfree, emit_qis_read_result,
};
use anyhow::Result;
use hugr::{
    HugrView, Node,
    extension::prelude::{option_type, qb_t},
    ops::ExtensionOp,
};
use hugr_llvm::{
    emit::{EmitFuncContext, EmitOpArgs},
    sum::LLVMSumValue,
    types::HugrSumType,
};
use tket_qsystem::extension::qsystem::QSystemOp;

use super::QirCodegenExtension;

impl QirCodegenExtension {
    pub fn emit_qsystem_op<'c, H: HugrView<Node = Node>>(
        &self,
        context: &mut EmitFuncContext<'c, '_, H>,
        args: EmitOpArgs<'c, '_, ExtensionOp, H>,
        op: QSystemOp,
    ) -> Result<()> {
        use QSystemOp::*;
        match op {
            Measure => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;

                let result_bool = emit_qis_read_result(context, result)?;
                args.outputs.finish(context.builder(), [result_bool])
            }
            LazyMeasure => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;

                let result_bool = emit_qis_read_result(context, result)?;
                let result_sum = LLVMSumValue::try_new(
                    result_bool,
                    context.llvm_sum_type(HugrSumType::new_unary(2))?,
                )?;

                let result_i32 = result_sum.build_get_tag(context.builder())?;
                let i1 = context.iw_context().bool_type();
                let result_i1 = context.builder().build_int_truncate(result_i32, i1, "")?;
                // futures are i1s, so this is fine
                args.outputs.finish(context.builder(), [result_i1.into()])
            }
            MeasureReset => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;
                let _ = emit_qis_gate(context, "__quantum__qis__reset__body", [], [qb])?;
                let result_bool = emit_qis_read_result(context, result)?;
                args.outputs.finish(context.builder(), [qb, result_bool])
            }
            LazyMeasureReset => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;
                let _ = emit_qis_gate(context, "__quantum__qis__reset__body", [], [qb])?;
                let result_bool = emit_qis_read_result(context, result)?;
                let result_sum = LLVMSumValue::try_new(
                    result_bool,
                    context.llvm_sum_type(HugrSumType::new_unary(2))?,
                )?;
                let result_i32 = result_sum.build_get_tag(context.builder())?;
                let i1 = context.iw_context().bool_type();
                let result_i1 = context.builder().build_int_truncate(result_i32, i1, "")?;
                args.outputs
                    .finish(context.builder(), [qb, result_i1.into()])
            }
            Rz => emit_qis_gate_finish(
                context,
                "__quantum__qis__rz__body",
                &args.inputs[1..2],
                &args.inputs[0..1],
                args.outputs,
            ),
            PhasedX => emit_qis_gate_finish(
                context,
                "__quantum__qis__phasedx__body",
                &args.inputs[1..3],
                &args.inputs[0..1],
                args.outputs,
            ),
            ZZPhase => emit_qis_gate_finish(
                context,
                "__quantum__qis__rzz__body",
                &args.inputs[2..3],
                &args.inputs[0..2],
                args.outputs,
            ),
            TryQAlloc => {
                let qb = emit_qis_qalloc(context)?;
                let option_ty = context.llvm_sum_type(option_type(qb_t()))?;
                let qb = option_ty.build_tag(context.builder(), 1, vec![qb])?.into();
                args.outputs.finish(context.builder(), [qb])
            }
            QFree => emit_qis_qfree(context, args.inputs[0]),
            Reset => emit_qis_gate_finish(
                context,
                "__quantum__qis__reset__body",
                [],
                &args.inputs,
                args.outputs,
            ),
            _ => anyhow::bail!("Unknown op: {op:?}"),
        }
    }
}

#[cfg(test)]
mod test {

    use hugr::ops::OpType;
    use hugr_llvm::{
        check_emission,
        test::{TestContext, llvm_ctx},
    };
    use rstest::rstest;

    use tket_qsystem::extension::qsystem::QSystemOp;

    use crate::qir::{QirCodegenExtension, QirPreludeCodegen};
    use crate::test::single_op_hugr;

    #[rstest::fixture]
    fn ctx(mut llvm_ctx: TestContext) -> TestContext {
        llvm_ctx.add_extensions(|builder| {
            builder
                .add_extension(QirCodegenExtension)
                .add_prelude_extensions(QirPreludeCodegen)
                .add_default_int_extensions()
                .add_float_extensions()
        });
        llvm_ctx
    }

    #[rstest]
    #[case(QSystemOp::MeasureReset)]
    #[case(QSystemOp::Reset)]
    #[case(QSystemOp::QFree)]
    #[case(QSystemOp::TryQAlloc)]
    #[case(QSystemOp::ZZPhase)]
    #[case(QSystemOp::PhasedX)]
    #[case(QSystemOp::Rz)]
    #[case(QSystemOp::LazyMeasure)]
    #[case(QSystemOp::LazyMeasureReset)]
    #[case(QSystemOp::Measure)]
    fn emit(ctx: TestContext, #[case] op: impl Into<OpType>) {
        let op = op.into();
        let mut insta = insta::Settings::clone_current();
        insta.set_snapshot_suffix(format!("{}_{}", insta.snapshot_suffix().unwrap_or(""), op));
        insta.bind(|| {
            use tket_qsystem::QSystemPass;

            let mut hugr = single_op_hugr(op);
            QSystemPass::default().run(&mut hugr).unwrap();
            check_emission!(hugr, ctx);
        })
    }
}
