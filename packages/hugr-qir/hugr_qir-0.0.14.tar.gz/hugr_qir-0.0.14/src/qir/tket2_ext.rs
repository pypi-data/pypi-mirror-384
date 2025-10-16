use crate::qir::{
    emit_qis_gate_finish, emit_qis_measure_to_result, emit_qis_qalloc, emit_qis_qfree,
    emit_qis_read_result,
};
use anyhow::{Result, bail};
use hugr::{HugrView, Node, ops::ExtensionOp};
use hugr_llvm::emit::{EmitFuncContext, EmitOpArgs};

use super::QirCodegenExtension;

impl QirCodegenExtension {
    #[allow(non_snake_case)]
    pub fn emit_tket_op<'c, H: HugrView<Node = Node>>(
        &self,
        context: &mut EmitFuncContext<'c, '_, H>,
        args: EmitOpArgs<'c, '_, ExtensionOp, H>,
        op: tket::TketOp,
    ) -> Result<()> {
        use tket::TketOp::*;
        match op {
            H => emit_qis_gate_finish(
                context,
                "__quantum__qis__h__body",
                [],
                args.inputs,
                args.outputs,
            ),
            CX => emit_qis_gate_finish(
                context,
                "__quantum__qis__cx__body",
                [],
                args.inputs,
                args.outputs,
            ),
            CY => emit_qis_gate_finish(
                context,
                "__quantum__qis__cy__body",
                [],
                args.inputs,
                args.outputs,
            ),
            CZ => emit_qis_gate_finish(
                context,
                "__quantum__qis__cz__body",
                [],
                args.inputs,
                args.outputs,
            ),
            T => emit_qis_gate_finish(
                context,
                "__quantum__qis__t__body",
                [],
                args.inputs,
                args.outputs,
            ),
            Tdg => emit_qis_gate_finish(
                context,
                "__quantum__qis__t__adj",
                [],
                args.inputs,
                args.outputs,
            ),
            S => emit_qis_gate_finish(
                context,
                "__quantum__qis__s__body",
                [],
                args.inputs,
                args.outputs,
            ),
            Sdg => emit_qis_gate_finish(
                context,
                "__quantum__qis__s__adj",
                [],
                args.inputs,
                args.outputs,
            ),
            X => emit_qis_gate_finish(
                context,
                "__quantum__qis__x__body",
                [],
                args.inputs,
                args.outputs,
            ),
            Y => emit_qis_gate_finish(
                context,
                "__quantum__qis__y__body",
                [],
                args.inputs,
                args.outputs,
            ),
            Z => emit_qis_gate_finish(
                context,
                "__quantum__qis__z__body",
                [],
                args.inputs,
                args.outputs,
            ),
            Rx => emit_qis_gate_finish(
                context,
                "__quantum__qis__rx__body",
                &args.inputs[1..2],
                &args.inputs[0..1],
                args.outputs,
            ),
            Ry => emit_qis_gate_finish(
                context,
                "__quantum__qis__ry__body",
                &args.inputs[1..2],
                &args.inputs[0..1],
                args.outputs,
            ),
            Rz => emit_qis_gate_finish(
                context,
                "__quantum__qis__rz__body",
                &args.inputs[1..2],
                &args.inputs[0..1],
                args.outputs,
            ),
            Reset => emit_qis_gate_finish(
                context,
                "__quantum__qis__reset__body",
                [],
                &args.inputs,
                args.outputs,
            ),
            Measure => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;

                let result_i1 = emit_qis_read_result(context, result)?;
                args.outputs.finish(context.builder(), [qb, result_i1])
            }
            MeasureFree => {
                let qb = args.inputs[0];
                // i.e. Result*
                let result = emit_qis_measure_to_result(context, qb)?;
                emit_qis_qfree(context, qb)?;
                let result_i1 = emit_qis_read_result(context, result)?;
                args.outputs.finish(context.builder(), [result_i1])
            }
            QAlloc => {
                let qb = emit_qis_qalloc(context)?;
                args.outputs.finish(context.builder(), [qb])
            }
            QFree => emit_qis_qfree(context, args.inputs[0]),
            _ => bail!("Unknown op: {op:?}"),
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
    use tket::TketOp;

    use crate::qir::boolcodegenextension_workaround::BoolCodegenExtension;
    use crate::test::single_op_hugr;
    use crate::{
        qir::{QirCodegenExtension, QirPreludeCodegen},
        rotation::RotationCodegenExtension,
    };

    #[rstest::fixture]
    fn ctx(mut llvm_ctx: TestContext) -> TestContext {
        llvm_ctx.add_extensions(|builder| {
            builder
                .add_extension(QirCodegenExtension)
                .add_prelude_extensions(QirPreludeCodegen)
                .add_extension(RotationCodegenExtension::new(QirPreludeCodegen))
                .add_extension(BoolCodegenExtension)
        });
        llvm_ctx
    }

    #[rstest]
    #[case(TketOp::QFree)]
    #[case(TketOp::QAlloc)]
    #[case(TketOp::MeasureFree)]
    #[case(TketOp::Measure)]
    #[case(TketOp::Reset)]
    #[case(TketOp::Rz)]
    #[case(TketOp::Ry)]
    #[case(TketOp::Rx)]
    #[case(TketOp::Z)]
    #[case(TketOp::Y)]
    #[case(TketOp::X)]
    #[case(TketOp::Sdg)]
    #[case(TketOp::S)]
    #[case(TketOp::Tdg)]
    #[case(TketOp::T)]
    #[case(TketOp::CX)]
    #[case(TketOp::CY)]
    #[case(TketOp::CZ)]
    fn emit(ctx: TestContext, #[case] op: impl Into<OpType>) {
        let op = op.into();
        let mut insta = insta::Settings::clone_current();
        insta.set_snapshot_suffix(format!("{}_{}", insta.snapshot_suffix().unwrap_or(""), op));
        insta.bind(|| {
            let hugr = single_op_hugr(op);
            check_emission!(hugr, ctx);
        })
    }
}
